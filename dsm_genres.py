# coding: utf-8
from flask import Flask
from flask import request, render_template
import os

app = Flask(__name__)

import ConfigParser
config = ConfigParser.RawConfigParser()
config.read('dsm_genres.cfg')

#todo: config is not working, fix it
#root = config.get('Files and directories', 'root')
print os.getcwd()
root = '/home/liza/PycharmProjects/dsm_genres/'
#modelsfile = config.get('Files and directories', 'models')
modelsfile = 'models.csv'
#temp = config.get('Files and directories', 'temp')
#tags = config.getboolean('Tags', 'use_tags')
tags = False
#lemmatize = config.getboolean('Other', 'lemmatize')
lemmatize = False
#dbpedia = config.getboolean('Other', 'dbpedia_images')
if lemmatize:
    from lemmatizer import freeling_lemmatizer
#taglist = set(config.get('Tags', 'tags_list').split())
#defaulttag = config.get('Tags', 'default_tag')
default_tag = 'S'
tags_list = 'S A NUM ANUM V ADV SPRO APRO ADVPRO PR CONJ PART INTJ UNKN'


our_models = {}
for line in open(root + modelsfile, 'r').readlines():
    if line.startswith("#"):
        continue
    res = line.strip().split('\t')
    (identifier, description, path, string, default) = res
    if default == 'True':
        defaultmodel = identifier
        our_models[identifier] = string


def process_query(userquery):
    userquery = userquery.strip().replace(u'ё', u'е')
    if tags:
        if '_' in userquery:
            query_split = userquery.split('_')
            if query_split[-1] in taglist:
                query = ''.join(query_split[:-1]).lower() + '_' + query_split[-1]
            else:
                return 'Incorrect tag!'
    else:
        if lemmatize:
            pos_tag = freeling_lemmatizer(userquery)
            if pos_tag == 'A' and userquery.endswith(u'о'):
                pos_tag = 'ADV'
            query = userquery.lower() + '_' + pos_tag
        else:
            return 'Incorrect tag!'
    return query


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/genres', methods=['GET', 'POST'])
def genres():
    if request.method == 'POST':
        input_data = 'dummy'
        try:
            input_data = request.form['query']
        except:
            pass
        if input_data != 'dummy' and input_data.replace('_', '').replace('-', '').isalnum():
            query = process_query(input_data)
            if query == "Incorrect tag!":
                return render_template('genres.html', error=query)
            model_value = request.form.getlist('model')
            if len(model_value) < 1:
                model = defaultmodel
            else:
                model = model_value[0]
            message = "1;" + query + ";" + 'ALL' + ";" + model
            result = '' #todo: get result
            associates_list = []
            if "unknown to the" in result or "No result" in result:
                return render_template('home.html', error=result.decode('utf-8'))
            else:
                output = result.split('&')
                associates = output[0]
                for word in associates.split():
                    w = word.split("#")
                    associates_list.append((w[0].decode('utf-8'), float(w[1])))

                return render_template('home.html', list_value=associates_list, word=query, model=model, tags=tags)
        else:
            error_value = u"Incorrect query!"
            return render_template("home.html", error=error_value, tags=tags)
    return render_template('home.html', tags=tags)


if __name__ == '__main__':
    app.run()
