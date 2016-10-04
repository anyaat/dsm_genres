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

import ConfigParser, socket

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
    our_models[identifier] = path


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
tags_list2= 'ADJ VERB SUBST UNC ADV'
taglist = set(tags_list2.split())

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
            print message
            associates = json.loads(serverquery(message))
            distances = {}
            for m in our_models:
                if m == 'all':
                    continue
                set_1 = set([x.split('#')[0] for x in associates['all']])
                set_2 = set([x.split('#')[0] for x in associates[m]])
                distance = 1 - jaccard(set_1, set_2)
                distances[m] = distance
            return render_template('home.html', result=associates, word=query.split('_')[0], pos=query.split('_')[-1], distances=distances)
    return render_template('home.html')

