#!/usr/local/python/bin/python2.7
# coding: utf-8

import socket, json
import sys, datetime
from thread import *
import sys, gensim, logging
from tagger import tagword, tagsentence
import numpy as np

import ConfigParser
config = ConfigParser.RawConfigParser()
config.read('dsm_genres.cfg')

root = config.get('Files and directories', 'root')
HOST = config.get('Sockets', 'host')  # Symbolic name meaning all available interfaces
PORT = config.getint('Sockets', 'port')  # Arbitrary non-privileged port
tags = config.getboolean('Tags', 'use_tags')

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


# Loading models

our_models = {}
for line in open(root + config.get('Files and directories', 'models'), 'r').readlines():
    if line.startswith("#"):
        continue
    res = line.strip().split('\t')
    (identifier, description, path, default) = res
    our_models[identifier] = path

models_dic = {}

for m in our_models:
    if our_models[m].endswith('.bin.gz'):
        models_dic[m] = gensim.models.Word2Vec.load_word2vec_format(our_models[m], binary=True)
    else:
        models_dic[m] = gensim.models.Word2Vec.load(our_models[m])
    print >> sys.stderr, "Model", m, "from file", our_models[m], "loaded successfully."

# Vector functions

def find_synonyms(query):
    (q, posfilter) = query
    results = {}
    lemma = q.split('_')[0]
    pos = q.split('_')[-1]
    for model in models_dic:
        m = models_dic[model]
        if not q in m:
            candidates_set = set()
            candidates_set.add(q.upper())
            if tags:
                candidates_set.add(lemma + '_UNKN')
                candidates_set.add(lemma.lower() + '_' + pos)
                candidates_set.add(lemma.capitalize() + '_' + pos)
            else:
                candidates_set.add(q.lower())
                candidates_set.add(q.capitalize())
            noresults = True
            for candidate in candidates_set:
                if candidate in m:
                    q = candidate
                    noresults = False
                    break
	    if noresults == True:
		results[model] = [q + " is unknown to the model"]
		continue
        	#return results, models
	if posfilter == 'ALL':
	    #results[model] = [i[0] + "#" + str(i[1]) for i in m.most_similar(positive=q, topn=10)]
	    results[model] = [(i[0], i[1]) for i in m.most_similar(positive=q, topn=30) if i[0].split('_')[-1] == pos][:10]
	else:
	    results[model] = [(i[0], i[1]) for i in m.most_similar(positive=q, topn=20) if i[0].split('_')[-1] == posfilter][:10]
        #if len(results) == 0:
        #    results[model] = ('No results')
    return results

def classify(text):
    text = text[0].strip()
    #text = text.decode('utf-8','replace')
    sentences = tagsentence(text.encode('ascii', 'replace'))
    results = {}
    for model in models_dic:
        m = models_dic[model]
        sc = m.score(sentences, total_sentences=len(sentences))
        sc = np.median(sc)
        sc = np.float(sc)
        results[model] = sc
    results['words'] = sentences
    return results

operations = {'1': find_synonyms, '2': classify}

# Bind socket to local host and port

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print >> sys.stderr, 'Socket created'

try:
    s.bind((HOST, PORT))
except socket.error, msg:
    print >> sys.stderr, 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()

print >> sys.stderr, 'Socket bind complete'

#Start listening on socket
s.listen(100)
print >> sys.stderr, 'Socket now listening on port', PORT

#Function for handling connections. This will be used to create threads
def clientthread(conn, addr):
    #Sending message to connected client
    conn.send('word2vec model server')  #send only takes string

    #infinite loop so that function do not terminate and thread do not end.
    while True:
        #Receiving from client
        data = conn.recv(1024)
        data = data.decode("utf-8")
	query = data.split(";")
        output = operations[query[0]]((query[1:]))
        if not data:
            break
        now = datetime.datetime.now()
        print >> sys.stderr, now.strftime("%Y-%m-%d %H:%M"), '\t', addr[0] + ':' + str(addr[1]), '\t', data
        if query[0] == "1" or query[0] == "2":
            reply = json.dumps(output)
            conn.sendall(reply.encode('utf-8'))
        break

    #came out of loop
    conn.close()

#now keep talking with the client
while 1:
    #wait to accept a connection - blocking call
    conn, addr = s.accept()

    #start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
    start_new_thread(clientthread, (conn, addr))

s.close()