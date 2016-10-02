#!/usr/bin/python
# coding: utf-8

import requests
import json

# Demands Stanford Core NLP server running on a defined port
# Start server with something like:
# java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer --port 9000

port = 9000
conversion = {"CC": "CONJ",
              "CD": "ADJ",
              "CD|RB": "UNC",
              "DT": "ART",
              "EX": "ART",
              "FW": "UNC",
              "IN": "PREP",
              "IN|RP": "PREP",
              "JJ": "ADJ",
              "JJR": "ADJ",
              "JJ|RB": "ADJ",
              "JJRJR": "ADJ",
              "JJS": "ADJ",
              "JJ|VBG": "ADJ",
              "LS": "UNC",
              "MD": "VERB",
              "NN|NNS": "SUBST",
              "NN": "SUBST",
              "NNP": "SUBST",
              "NNPS": "SUBST",
              "NNS": "SUBST",
              "NN|SYM": "SUBST",
              "NN|VBG": "SUBST",
              "NP": "SUBST",
              "PDT": "ART",
              "POS": "PRT",
              "PRP": "PRON",
              "PRP$": "PRON",
              "PRP|VBP": "PRON",
              "PRT": "PRT",
              "RB": "ADV",
              "RBR": "ADV",
              "RB|RP": "ADV",
              "RBS": "ADV",
              "RB|VBG": "ADV",
              "RN": "UNC",
              "RP": "PREP",
              "SYM": "UNC",
              "TO": "PREP",
              "VBD|VBN": "VERB",
              "VBD": "VERB",
              "VBG|NN": "VERB",
              "VBG": "VERB",
              "VBN": "VERB",
              "VBP|TO": "VERB",
              "VBP": "VERB",
              "VB": "VERB",
              "VBZ": "VERB",
              "VP": "VERB",
              "WDT": "ART",
              "WH": "UNC",
              "WP": "PRON",
              "WP$": "PRON",
              "WRB": "ADV",
              "UH": "INTERJ"}


def tagsentence(sentence):
    tagged = requests.post(
        'http://localhost:%s/?properties={"annotators": "tokenize,ssplit,pos,lemma", "outputFormat": "json"}' % port,
        data=sentence).text
    dictionary = json.loads(tagged)
    tokens = dictionary["sentences"][0]["tokens"]
    print tokens
    lemmas = []
    for token in tokens:
        lemma = token['lemma'].lower()
        pos = token['pos']
        if pos in conversion:
            pos = conversion[pos]
        lemmas.append(lemma + '_' + pos)
    return lemmas


def tagword(word):
    tagged = requests.post(
        'http://localhost:%s/?properties={"annotators": "tokenize,ssplit,pos,lemma", "outputFormat": "json"}' % port,
        data=word).text
    dictionary = json.loads(tagged)
    tokens = dictionary["sentences"][0]["tokens"]
    lemma = tokens[0]['lemma'].lower()
    pos = tokens[0]['pos']
    if pos in conversion:
        pos = conversion[pos]
    output = lemma + '_' + pos
    return output

print tagword('cup')