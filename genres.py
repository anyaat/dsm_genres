#!/usr/bin/python
# coding: utf-8

import sys, gensim, logging,codecs, os
from itertools import combinations

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

def jaccard(set_1, set_2):
    n = len(set_1.intersection(set_2))
    return n / float(len(set_1) + len(set_2) - n)


model_files = [f for f in os.listdir('.') if f.endswith('win10.model') and f.startswith('bnc')]

models = {}

for m in model_files:
    model = gensim.models.Word2Vec.load(m)
    model.init_sims(replace=True)
    models[m.split('.')[0]] = model

while True:
    try:
        query = raw_input("Enter your word:").decode(sys.stdin.encoding)
    except:
        continue
    if query == "exit":
        exit()
    word = query.strip()
    associates = {}
    print word
    for m in models:
        model = models[m]
        associates[m] = set()
        if word in model:
            print m, '===='
	    for i in model.most_similar(positive=[word], topn=10):
                print i[0],i[1]
                associates[m].add(i[0])
	    print '====='
	else:
	    print word,'is not present in the model', m
    print 'Distances:'
    for pair in combinations(models.keys(), 2):
	distance = 1 - jaccard(associates[pair[0]], associates[pair[1]])
	print pair[0],'VS', pair[1]+':', distance
	
