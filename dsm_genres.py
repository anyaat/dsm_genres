#!/ltg/python/bin/python2.7
# coding: utf-8
import logging
import hashlib
import os
import sys
import json
from flask import render_template, Blueprint, redirect, Response
from flask import request
import numpy as np
import gensim
from collections import OrderedDict
from tagger import tagsentence, tagword

import hashlib
import seaborn as sns 
import networkx as nx
import matplotlib.pyplot as plt
from itertools import combinations
from dm_graphs import graph_reduce, MST_pathfinder
from gensim.models import Word2Vec

import ConfigParser, socket
import operator

sns.set_style('white')

config = ConfigParser.RawConfigParser()
config.read('dsm_genres.cfg')

root = '/home/andreku/www/RegisterExplorer/'
modelsfile = 'models.csv'
our_models = {}
for line in open(root + modelsfile, 'r').readlines():
    if line.startswith("#"):
	continue
    res = line.strip().split('\t')
    (identifier, description, path, default) = res
    our_models[identifier] = description


logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

tags = True
lemmatize = True
if lemmatize:
    from tagger import tagword, tagsentence
    
# Establishing connection to model server
host = config.get('Sockets', 'host')
port = config.getint('Sockets', 'port')
try:
    remote_ip = socket.gethostbyname(host)
except socket.gaierror:
    # could not resolve
    print >> sys.stderr, 'Hostname could not be resolved. Exiting'
    sys.exit()

default_tag = 'SUBST'
taglist = set(config.get('Tags', 'tags_list').split())
defaulttag = config.get('Tags', 'default_tag')


genre = Blueprint('genres', __name__, template_folder='templates')

def jaccard(set_1, set_2):
    n = len(set_1 & set_2)
    return n / float(len(set_1) + len(set_2) - n)

def process_query(userquery):
    userquery = userquery.strip()
    if tags:
        if '_' in userquery:
            query_split = userquery.split('_')
            if query_split[-1] in taglist:
                query = ''.join(query_split[:-1]).lower() + '_' + query_split[-1]
            else:
                return 'Incorrect tag!'
        else:
            if lemmatize:
                query = tagword(userquery)
            else:
                return 'Incorrect tag!'
    return query

def serverquery(message):
    # create an INET, STREAMing socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print >> sys.stderr, 'Failed to create socket'
        return None

    # Connect to remote server
    s.connect((remote_ip, 15666))
    # Now receive data
    reply = s.recv(1024)

    # Send some data to remote server
    try:
        s.sendall(message.encode('utf-8'))
    except socket.error:
        # Send failed
        print >> sys.stderr, 'Send failed'
        s.close()
        return None
    # Now receive data
    reply = s.recv(32768)
    s.close()
    return reply

def plot(m, model_path, query, associates):
    model = Word2Vec.load(model_path)
    ass_set = set([x[0] for x in associates[m]])
    edges = ((a.split('_')[0], b.split('_')[0], model.similarity(a,b)) for a, b in combinations(ass_set, 2))
    G = nx.Graph()
    G.add_weighted_edges_from(edges)
    NG = graph_reduce(G)
    MST = MST_pathfinder(NG)
    pos = nx.spring_layout(MST)
    nx.draw_networkx_nodes(MST, pos, node_size=100, node_color='#3498db', alpha=0.3)
    nx.draw_networkx_edges(MST, pos, width=2, alpha=0.4, edge_color='#3498db')
    nx.draw_networkx_labels(MST, pos, font_size=12, font_color='#34495e', font_family='sans-serif', weight='bold')
    plt.title(m, fontsize=16, fontweight='bold')
    mm = hashlib.md5()
    name = m + '_' + query.encode('ascii', 'backslashreplace')
    mm.update(name)
    plt.savefig(root + 'plots/' + name + '.png', dpi=150, bbox_inches='tight')
    plt.clf()

@genre.route('/embeddings/registers/', methods=['GET', 'POST'])
def genrehome():
    if request.method == 'POST':
        input_data = 'dummy'
        try:
            input_data = request.form['query']
        except:
            pass
        if input_data != 'dummy' and input_data.replace('_', '').replace('-', '').isalnum():
            query = process_query(input_data)
            if query == 'Incorrect tag!':
                error = query
                return render_template('home.html', error=error)
            message = "1;" + query + ";" + 'ALL'
            associates = json.loads(serverquery(message))
            distances = {}
            for m in our_models:
                plotfile = "%s_%s.png" % (m, query)
                if not os.access(root + '/plots/' + plotfile, os.F_OK):
                    print >> sys.stderr, 'No previous image found'
                    plot(m, our_models[m], query, associates)
                if m == 'all':
                    continue
                set_1 = set([x[0] for x in associates['all']])
                set_2 = set([x[0] for x in associates[m]])
                distance = 1 - jaccard(set_1, set_2)
                distances[m] = distance 
            distances_r = sorted(distances.items(), key=operator.itemgetter(1), reverse=True)
            return render_template('home.html', result=associates, word=query.split('_')[0], pos=query.split('_')[-1], distances=distances_r, models=our_models)
    return render_template('home.html')

@genre.route('/embeddings/registers/text/', methods=['GET', 'POST'])
def genretext():
    if request.method == 'POST':
        input_data = 'dummy'
        try:
            input_data = request.form['textquery']
        except:
            pass
        if input_data != 'dummy':
            query = input_data.strip().replace('\r\n',' ')
            message = "2;" + query
            result = json.loads(serverquery(message))
            lemmas = result['words']
            result.pop('words')
            ranking = sorted(result.items(), key=operator.itemgetter(1), reverse=True)
            return render_template('text.html', result=ranking, text=input_data, models=our_models, lemmas=lemmas, tags=taglist)
    return render_template('text.html')

@genre.route('/embeddings/registers/word/<word>/', methods=['GET', 'POST'])
def genreword(word):
    if request.method == 'POST':
        input_data = 'dummy'
        try:
            input_data = request.form['query']
        except:
            pass
    input_data = word
    if input_data != 'dummy' and input_data.replace('_', '').replace('-', '').isalnum():
	query = process_query(input_data)
        if query == 'Incorrect tag!':
	    error = query
            return render_template('home.html', error=error)
        message = "1;" + query + ";" + 'ALL'
        associates = json.loads(serverquery(message))
        distances = {}
        for m in our_models:
            plotfile = "%s_%s.png" % (m, query)
            if not os.access(root + '/plots/' + plotfile, os.F_OK):
                print >> sys.stderr, 'No previous image found'
                plot(m, our_models[m], query, associates)
            if m == 'all':
                continue
            set_1 = set([x[0] for x in associates['all']])
            set_2 = set([x[0] for x in associates[m]])
            distance = 1 - jaccard(set_1, set_2)
            distances[m] = distance
        distances_r = sorted(distances.items(), key=operator.itemgetter(1), reverse=True)
        return render_template('home.html', result=associates, word=query.split('_')[0], pos=query.split('_')[-1], distances=distances_r, models=our_models)
    return render_template('home.html')