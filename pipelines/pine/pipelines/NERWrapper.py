# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import argparse
import os
import json
from redis import Redis
import requests
import time
import uuid

from .pmap_ner import NER
from . import RankingFunctions as rank

# IMPORTANT: This class probably no longer works, but it doesn't seem to be used anywhere.

class NERWrapper:
    eve_headers = {'Content-Type': 'application/json'}

    def __init__(self, classifier_type, model_dir='models', entry_point='localhost:5000'):
        if classifier_type == 'opennlp':
            self.classifier_type = 'opennlp'
            self.file_extension = '.bin'
        else:
            self.classifier_type = 'corenlp'
            self.file_extension = '.ser.gz'

        #Classifier parameters
        self.model_dir=model_dir

        #EVE parameters
        self.entry_point=entry_point

        self.classifiers = {}

    def load_classifier(self, classifier_id):
        #get filename from eve
        classifier_obj = self.get_obj('classifiers', classifier_id)
        if classifier_obj is None:
            raise Exception("No classifier obj")
        if 'filename' not in classifier_obj:
            raise Exception('No filename in classifier obj')
        filename = os.path.join(self.model_dir, classifier_obj['filename'])
        if os.path.exists(filename):
            classifier = NER('opennlp')
            classifier.load_model(filename)
            print("Loaded classifier", classifier)
            self.classifiers[classifier_id] = classifier
        else:
            raise Exception('File Not Found')

    def predict(self, classifier_id, documents, document_ids):
        if classifier_id not in self.classifiers:
            try:
                self.load_classifier(classifier_id)
            except:
                return None
        classifier = self.classifiers[classifier_id]
        if len(documents) == len(document_ids):
            print(documents)
            print(document_ids)
            return classifier.predict(documents, document_ids)
        return None

    def update_model(self, classifier_id):
        #get classifier object
        classifier_obj = self.get_obj('classifiers', classifier_id)
        if classifier_obj is None:
            return
        collection_id = classifier_obj['collection_id']
        pipeline_parameters = classifier_obj['parameters']
        #pipeline_parameters = {}
        #pipeline_parameters['labels'] = classifier_obj['labels']

        print("Got classifier object", classifier_obj)

        #get documents
        query = 'documents?where={"overlap":0,"collection_id":"%s"}' % (collection_id)
        doc_map = {}
        while True:
            items, query = self.get_items(query)
            for d in items:
                doc_map[d['_id']] = d['text']
            if query is None:
                break
        print("Got documents")

        documents = []
        labels = []
        ann_ids=[]
        #get annotations and make data
        query = 'annotations?where={"collection_id":"%s"}' % (collection_id)
        while True:
            items, query = self.get_items(query)

            for a in items:
                docid = a['document_id']
                #remove overlaps
                if docid not in doc_map:
                    continue
                ann_ids.append(docid)
                labels.append(a['annotation'])
                documents.append(doc_map[docid])
            if query is None:
                break

        print("Got annotations")

        #train classifier
        classifier = NER(self.classifier_type)
        if pipeline_parameters is not None:
            classifier.fit(documents, labels, **pipeline_parameters)
        else:
            classifier.fit(documents, labels)
        print("Trained classifier")

        #save classifier
        filename = classifier_id + str(uuid.uuid4()) + self.file_extension
        classifier.save_model(os.path.join(self.model_dir, filename))
        #update filename in classifier on eve
        if not self.update('classifiers', classifier_id, classifier_obj['_etag'], {'filename': filename}):
            return False
        print("Saved classifier", filename)

        #re rank documents
        documents_no_anns = []
        ids_no_anns = list(set(doc_map.keys()).difference(set(ann_ids)))
        for id in ids_no_anns:
            documents_no_anns.append(doc_map[id])

        #classifier.load_model(os.path.join(self.model_dir, filename))
        #ranks = classifier.next_example(documents_no_anns, ids_no_anns)
        results = classifier.predict_proba(documents_no_anns, ids_no_anns)
        ranks = rank.least_confidence_squared(results)
        print("Ranks:", ranks)
        #Save updates to eve
        query = 'next_instances?where={"classifier_id":"%s"}' % (classifier_id)
        update_obj = self.get_items(query)[0]
        etag = update_obj[0]['_etag']
        id = update_obj[0]['_id']
        print("Updating next instances:")
        return self.update('next_instances', id, etag, {'document_ids':ranks})


    def update(self, resource, id, etag, update_obj):
        headers = {'Content-Type': 'application/json', 'If-Match': etag}
        r = requests.patch('http://%s/%s/%s' % (self.entry_point, resource, id),
                           json.dumps(update_obj),headers=headers)
        if r.status_code != 200:
            return False
        return True

    def get_obj(self, resource, id):
        url = 'http://%s/%s/%s' % (self.entry_point, resource, id)
        response = requests.get(url, headers=self.eve_headers)
        if response.status_code == 200:
            r = response.json()
            return r
        return None

    def get_all_items(self, resource):
        total = []
        while True:
            items, query = self.get_items(query)
            total.extend(items)
            if query is None:
                break
        return total

    def get_all_ids(self, resource):
        total_ids = []
        while True:
            items, query = self.get_items(query)
            for item in items:
                if '_id' in item:
                    total_ids.append(item['_id'])
            if query is None:
                break

        return total_ids

    def get_items(self, resource):
        url = 'http://%s/%s' % (self.entry_point, resource)
        response = requests.get(url, headers=self.eve_headers)
        if response.status_code == 200:
            r = response.json()
            if '_items' in r:
                if '_links' in r and 'next' in r['_links']:
                    return r['_items'], r['_links']['next']['href']
                else:
                    return r['_items'], None
        return [], None


if __name__ == '__main__':
    '''
    #Queue Information
    REDIS_HOST='localhost'
    REDIS_PORT=6379
    #This is pipeline ID
    REDIS_WORK_QUEUE = '5ba8faed4eb7dd32a4d6760c'

    #EVE Information
    entry_point='localhost:5000'

    #Model Storage
    model_dir = 'models'
    '''
    parser = argparse.ArgumentParser(description='Document classifier service')
    parser.add_argument('--redis', type=str, required=True, help='Redis server')
    parser.add_argument('--eve', type=str, required=True, help='Eve entrypoint')
    parser.add_argument('--port', type=int, default=6379, help='Redis port')
    parser.add_argument('--queue', type=str, required=True, help='Redis queue to subscribe to.  Pipeline ID')
    parser.add_argument('--models', type=str, default='/models', help='Path to model storage')
    parser.add_argument('--classifier', choices=['corenlp', 'opennlp'], default='opennlp', help='CoreNLP or OpenNLP NER Library')

    args = parser.parse_args()
    args = vars(parser.parse_args())
    wrapper = NERWrapper(args['classifier'], model_dir=args['models'], entry_point=args['eve'])

    channel = args['queue'] + "_pubsub"
    channel_bytes = bytes(channel, encoding='utf-8')
    redis = Redis(host=args['redis'], port=args['port'])
    pubsub = redis.pubsub()
    pubsub.subscribe(channel)

    while 1:
        msg = pubsub.get_message()
        if msg is not None and msg['type'] == 'message' and msg['channel']==channel_bytes:
            classifier_id = msg['data'].decode()
            wrapper.classifiers.pop(classifier_id, None)
            print("Updated classifier", classifier_id)

        if redis.llen(args['queue'] )>0:
            #two types of models fit/update and predict
            msg = json.loads(redis.lpop(args['queue'] ).decode())
            classifier_id = msg['classifier_id']
            print(msg)
            #use rpush to add to queue
            #train message: {'type':'train', 'classifier_id':'classifier_id'}
            #predict message: {'type':'predict', 'classifier_id':'classifier_id', 'documents':[], 'document_ids':[], 'response_key':'response_key'}

            if msg['type'] == 'train':
                if wrapper.update_model(classifier_id):
                    #send pub sub message
                    redis.publish(channel, classifier_id)
                    print("Successfully trained classifier")
            else:
                #predict
                output = wrapper.predict(classifier_id, msg['documents'], msg['document_ids'])
                redis.set(msg['response_key'], json.dumps(output), ex=240)
                print("Predicted:", classifier_id)

        time.sleep(0.005)

#pipeline id: '5ba13b214eb7dd654189551a'
#message with {'type':'train', 'classifier_id':'5ba13b214eb7dd65418955b2'}
