 # -*- coding: utf-8 -*-
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

"""
    eve-demo-client
    ~~~~~~~~~~~~~~~
    Simple and quickly hacked together, this script is used to reset the
    eve-demo API to its initial state. It will use standard API calls to:
        1) delete all items in the 'people' and 'works' collections
        2) post multiple items in both collection
    I guess it can also serve as a basic example of how to programmatically
    manage a remote API using the phenomenal Requests library by Kenneth Reitz
    (a very basic 'get' function is included even if not used).
    :copyright: (c) 2015 by Nicola Iarocci.
    :license: BSD, see LICENSE for more details.
"""
import sys
import json
import requests
import csv
import pprint
import time
import random
import os

from sklearn.datasets import fetch_20newsgroups
from random import randrange
from pymongo import MongoClient

if os.environ.get("FLASK_PORT"):
    FLASK_PORT = int(os.environ.get("FLASK_PORT"))
else:
    FLASK_PORT = 5000

if os.environ.get("MONGO_PORT"):
    MONGO_PORT = int(os.environ.get("MONGO_PORT"))
else:
    MONGO_PORT = 27017

ENTRY_POINT = '127.0.0.1:{}'.format(FLASK_PORT)
OVERLAP = .15
categories = ['alt.atheism', 'soc.religion.christian', 'comp.graphics', 'sci.med']
data = fetch_20newsgroups(subset='test', categories=categories, shuffle=True, random_state=42)
#data.data, data.target

def create_collection(userid, labels):
    collection = [{
            'creator_id': userid,
            'annotators': [userid],
            'viewers': [userid],
            'labels':labels,
            'metadata': {'title':'Trial Collection', 'description':'This is a sample description of a collection'},
            'archived': False,
            'configuration': {
                'allow_overlapping_ner_annotations': True
            }
        }]
    r = perform_post('collections', json.dumps(collection))
    return get_ids(r)

def create_documents(collection_id, user_id, num_docs):
    data = fetch_20newsgroups(subset='test', categories=categories, shuffle=False)

    docs = []
    for i in range(num_docs):
        docs.append({
            'creator_id': user_id,
            'collection_id': collection_id,
            'overlap': 0,
            'text': data.data[i]
        })
    r = perform_post('documents', json.dumps(docs))
    print('Created:', len(docs), 'documents')
    return get_ids(r)

def create_annotations(user_id, collection_id, doc_ids, categories):
    data = fetch_20newsgroups(subset='test', categories=categories, shuffle=False)

    annotations = []
    for i, doc_id in enumerate(doc_ids):
        annotations.append({
                'creator_id': user_id,
                'collection_id': collection_id,
                'document_id': doc_id,
                'annotation': [categories[data.target[i]]]
        })
    r = perform_post('annotations', json.dumps(annotations))
    print('Created:', len(annotations), 'annotations')
    return get_ids(r)

def update_annotations(annotation_ids):
    #perform_get('annotations?where={"document_id": {"$in": ["5b3531a9aec9104c8a9aca9e", "5b3531a9aec9104c8a9acaa0"]}}'
    for id in annotation_ids:
        url = 'http://'+ENTRY_POINT+'/annotations/'+id
        response = requests.get(url, headers={'Content-Type': 'application/json'})
        if response.status_code == 200:
            r = response.json()
            etag = r['_etag']
            headers = {'Content-Type': 'application/json', 'If-Match': etag}
            data = {'annotation': ['soc.religion.christian']}
            requests.patch('http://'+ENTRY_POINT+'/annotations/' + id, json.dumps(data), headers=headers)

def create_pipeline():
    pipeline = [
    {
        "_id": "5babb6ee4eb7dd2c39b9671c",
        "title": "Apache OpenNLP Named Entity Recognition",
        "description": "Apache's open source natural language processing toolkit for named entity recognition (NER).  See https://opennlp.apache.org/ for more information.  This is the default pipeline used for NER.",
        "name":"opennlp",
        "parameters":{
            "cutoff":"integer",
            "iterations":"integer"
        }
    },
    {
        "_id": "5babb6ee4eb7dd2c39b9671d",
        "title": "SpaCy Named Entity Recognition",
        "description": "spaCy is a free open-source library for Natural Language Processing in Python. It features NER, POS tagging, dependency parsing, word vectors and more",
        "name": "spaCy",
        "parameters": {
            "n_iter": "integer",
            "dropout": "float"
        }
    },
    {
        "_id": "5babb6ee4eb7dd2c39b9671f",
        "title": "Stanford CoreNLP Named Entity Recognition",
        "description": "Stanford's natural language processing toolkit for named entity recognition (NER).  See https://stanfordnlp.github.io/CoreNLP/ for more information.",
        "name":"corenlp",
        "parameters": {
            "max_left":"integer",
            "use_class_feature": [True, False],
            "use_word": [True, False],
            "use_ngrams": [True, False],
            "no_mid_ngrams": [True, False],
            "max_ngram_length":"integer",
            "use_prev": [True, False],
            "use_next": [True, False],
            "use_disjunctive": [True, False],
            "use_sequences": [True, False],
            "use_prev_sequences": [True, False],
            "use_type_seqs": [True, False],
            "use_type_seqs2": [True, False],
            "use_type_y_sequences": [True, False]
        }
    }
    ]
    r = perform_post('pipelines', json.dumps(pipeline))
    return get_ids(r)

def create_user():
    users = []
    users.append(
        {
            '_id':'bchee1',
            'firstname': "Brant",
            'lastname': 'Chee',
            'email': 'bchee1@jhmi.edu',
            'description': "Brant Developer",
            'role': ['user']
        })
    users.append({
            '_id': 'bchee2',
            'firstname': "Brant",
            'lastname': 'Chee',
            'email': 'bchee2@jhmi.edu',
            'description': "Brant administrator",
            'role': ['administrator']
    })
    users.append(
        {
            '_id': 'lglende1',
            'firstname': "Laura",
            'lastname': 'Glendenning',
            'email': 'lglende1@jh.edu',
            'description': "Developer Laura",
            'role': ['user']
        })
    users.append(
        {
            '_id': 'cahn9',
            'firstname': "Charles",
            'lastname': 'Ahn',
            'email': 'cahn9@jh.edu',
            'description': "Developer Charles",
            'role': ['user']
        })
    r = perform_post('users', json.dumps(users))
    return get_ids(r)

def create_classifier(collection_id, overlap, pipeline_id, labels):
    '''{
        'collection_id': {'type': 'objectid', 'required': True},
        'overlap': {'type': 'float', 'required': True},
        'pipeline_id': {'type': 'objectid', 'required': True},
        'parameters': {'type': 'dict'}'''
    classifier_obj = {'collection_id':collection_id,
                      'overlap':overlap,
                      'pipeline_id':pipeline_id,
                      'parameters':{"cutoff":1, "iterations":100},
                      'labels':labels
                      }
    r = perform_post('classifiers', json.dumps(classifier_obj))
    return get_ids(r)

def create_metrics(collection_id, classifier_id):
    # create metrics for classifier
    metrics_obj = {"collection_id": collection_id,
                      "classifier_id": classifier_id,
                      "documents": list(),
                      "annotations": list()
                      }
    metrics_resp = perform_post("metrics", json.dumps(metrics_obj))
    return get_ids(metrics_resp)

def create_next_ids(classifier_id, ann_ids, docids, overlap):
    num_overlap = int(len(docids) * overlap)
    #we're lazy and taking to first n docs as overlap
    #'classifier_id': {'type': 'objectid', 'required': True},
    #'document_ids': {'type': 'list', 'required': True},
    #'overlap_document_ids': {'type': 'dict', 'required': True}
    overlap_obj = {'classifier_id':classifier_id, 'document_ids':docids[num_overlap:], 'overlap_document_ids':{}}
    for id in ann_ids:
        overlap_obj['overlap_document_ids'][id] = docids[0:num_overlap]
    r = perform_post('next_instances', json.dumps(overlap_obj))
    return get_ids(r)

def get_ids(response):
    valids = []
    #print("Response:", response)
    if response.status_code == 201:
        r = response.json()
        if r['_status'] == 'OK':
            if '_items' in r:
                for obj in r['_items']:
                    if obj['_status'] == "OK":
                        valids.append(obj['_id'])
            else:
                valids.append(r['_id'])
    return valids

def perform_get(resource, data):
    headers = {'Content-Type': 'application/json'}
    return requests.get(endpoint(resource), data, headers=headers)

def perform_post(resource, data):
    headers = {'Content-Type': 'application/json'}
    return requests.post(endpoint(resource), data, headers=headers)

def endpoint(resource):
    url = 'http://%s/%s/' % (
        ENTRY_POINT if not sys.argv[1:] else sys.argv[1], resource)
    return url

def delete_database(mongourl, database):
    client = MongoClient(mongourl)
    client.drop_database(database)

def create_bionlp_annotations(bionlpfile, num_docs, pipeline_id, creator_id, annotator_ids):
    docs, anns, stats = load_bionlp(bionlpfile, num_docs)
    categories = list(stats.keys())

    #Create collection
    collection = [{
            'creator_id': creator_id,
            'annotators': annotator_ids,
            'viewers': annotator_ids,
            'labels':categories,
            'metadata': {'title':'NER Test Collection', 'description':'This is a sample sample collection to test NER tasks'},
            'archived': False,
            'configuration': {
                'allow_overlapping_ner_annotations': True
            }
        }]
    r = perform_post('collections', json.dumps(collection))
    collection_id = get_ids(r)
    collection_id = collection_id[0]
    print("collection_id", collection_id)

    #Create documents
    images = [
        'https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Unequalized_Hawkes_Bay_NZ.jpg/600px-Unequalized_Hawkes_Bay_NZ.jpg',
        'https://cdn.indreams.me/cdf00b6d4827cd66511bdc35e1ef2ea3_10',
        '/static/apl.png',
        '/static/campus.jpg'
        ]
    upload = []
    for i in range(len(docs)):
        upload.append({
            'creator_id': creator_id,
            'collection_id': collection_id,
            'overlap': 0,
            'text': docs[i],
            'metadata': { 'imageUrl': images[randrange(0,len(images))] }
        })
    r = perform_post('documents', json.dumps(upload))
    print('Created:', len(upload), 'documents')
    doc_ids = get_ids(r)

    classifier_ids = create_classifier(collection_id, 0, pipeline_id, categories)
    print('Classifier id', classifier_ids)
    metrics_ids = create_metrics(collection_id, classifier_ids[0])
    print('Metrics id', metrics_ids)
    next_ids = create_next_ids(classifier_ids[0], annotator_ids, doc_ids, 0)
    annotations = []

    for i, doc_id in enumerate(doc_ids):
        annotations.append({
                'creator_id': annotator_ids[random.randrange(0, len(annotator_ids))],
                'collection_id': collection_id,
                'document_id': doc_id,
                'annotation': anns[i]
        })
    r = perform_post('annotations', json.dumps(annotations))
    print('Created:', len(annotations), 'annotations')
    return get_ids(r)

def load_bionlp(csvname, limit):
     docs = []
     anns = []
     stats = {}
     sentences_per_doc = 10  # total of 47959 sentences
     with open(csvname, 'r', encoding='utf-8', errors='ignore') as csv_file:
         csv_reader = csv.reader(csv_file, delimiter=',')
         line_count = 0
         doc_text = ''
         doc_anns = []
         sentence_id = 1
         next(csv_reader)
         for line in csv_reader:
             if line[0] != '':
                 sentence_id = int(line[0].split(':')[1])
                 # avoids triggering on the first sentence
                 if sentence_id % sentences_per_doc == 1 and sentence_id >= sentences_per_doc:  # once you have enough sentences per doc, append to list and clear doc_text/doc_anns
                    # print('Added case ' + cases[-1])
                    docs.append(doc_text)
                    doc_text = ''
                    anns.append(doc_anns)
                    doc_anns = []
                    if len(docs) > limit-2:
                        break
             token = line[1]
             # add token to text and record start/end char
             start_char = len(doc_text)
             doc_text += token
             end_char = len(doc_text)
             doc_text += ' '

             if line[3] != 'O':  # if label is not 'O'
                 label = line[3].split('-')[1]  # has BILUO tages that we don't need ex. 'B-tag'
                 if label not in stats:
                     stats[label] = 0
                 if line[3].split('-')[0] == 'B':
                     stats[label] += 1  # only add if the label has the 'begin' tag otherwise labels spanning multiple tokens are added multiple times
                     doc_anns.append((start_char, end_char, label))  # add label to annotations
                 elif line[3].split('-')[0] == 'I':
                     # NOTE: assumes I-tags only ever follow B-tags, will break if not the case
                     doc_anns.append((doc_anns[-1][0], end_char,
                                      label))  # if the label spans multiple tokens update the most recent annotation with the new end char
                     del doc_anns[-2]
             line_count += 1
             # add remaining sentence
         docs.append(doc_text)
         doc_text = ''
         anns.append(doc_anns)
         doc_anns = []
     return docs, anns, stats

if __name__ == '__main__':
    mongourl = 'mongodb://localhost:{}'.format(MONGO_PORT)
    delete_database(mongourl, 'test') # old database
    delete_database(mongourl, 'pmap_nlp')

    #generate new data
    user_ids = create_user()
    pipeline_ids = create_pipeline()
    collection_id = create_collection(user_ids[1], categories)
    doc_ids = create_documents(collection_id[0], user_ids[1], 750)
    classifier_ids = create_classifier(collection_id[0], OVERLAP, pipeline_ids[0], categories)
    metrics_ids = create_metrics(classifier_ids[0],collection_id[0])
    next_ids = create_next_ids(classifier_ids[0], [user_ids[1]], doc_ids, OVERLAP)
    annotation_ids = create_annotations(user_ids[0], collection_id[0], doc_ids[int(len(doc_ids)/2):], categories)
    print("collection_id=",collection_id[0])
    print("classifier_id='", classifier_ids[0], "'")
    print("metrics_id='", metrics_ids[0], "'")
    #update_annotations(annotation_ids[int(len(annotation_ids)/2):])

    collection_id2 = create_collection(user_ids[1], categories)
    doc_ids2 = create_documents(collection_id2[0], user_ids[1], 500)
    annotation_ids2 = create_annotations(user_ids[0], collection_id[0], doc_ids2 , categories)
    update_annotations(annotation_ids2[0:int(len(annotation_ids2) / 2)])

    print('user_ids=',user_ids)
    print('pipeline_ids=',pipeline_ids)
    print('collection_id=',collection_id)
    print('doc_ids=',doc_ids)
    print('classifier_ids=',classifier_ids)
    print('next_ids=',next_ids)
    print('annotation_ids1=', annotation_ids)
    print('annotation_ids2=',annotation_ids2)
    print('collection_id2=', collection_id2)
    print('doc_ids2=', doc_ids2)

    ner_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ner_dataset.csv')

    #user_ids = create_user()
    #pipeline_ids = create_pipeline()
    #print('user_ids', user_ids)
    #print('pipeline_ids', pipeline_ids)
    create_bionlp_annotations(ner_file, 150, pipeline_ids[1], user_ids[0], user_ids)
