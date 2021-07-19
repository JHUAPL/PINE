# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import json
import logging
import requests
import typing

from .shared.config import ConfigBuilder

logger = logging.getLogger(__name__)
config = ConfigBuilder.get_config()

class EveClient(object):
    eve_headers = {'Content-Type': 'application/json'}

    def __init__(self, entry_point='{}:{}'.format(config.EVE_HOST, config.EVE_PORT)):
        self.entry_point = entry_point

    def add(self, resource, add_object):
        headers = {'Content-Type': 'application/json'}
        r = requests.post('http://%s/%s/' % (self.entry_point, resource),
                           json.dumps(add_object),headers=headers)
        if r.status_code != 200:
            return False
        return r.json()["_id"]

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
            items, query = self.get_items(resource)
            total.extend(items)
            if query is None:
                break
        return total

    def get_all_ids(self, resource):
        total_ids = []
        while True:
            items, query = self.get_items(resource)
            for item in items:
                if '_id' in item:
                    total_ids.append(item['_id'])
            if query is None:
                break

        return total_ids

    def get_items(self, resource, params={}):
        url = 'http://%s/%s' % (self.entry_point, resource)
        response = requests.get(url, params=params, headers=self.eve_headers)
        if response.status_code == 200:
            r = response.json()
            if '_items' in r:
                if '_links' in r and 'next' in r['_links']:
                    return r['_items'], r['_links']['next']['href']
                else:
                    return r['_items'], None
        return [], None

    def _get_documents_map(self, params: dict = {}):
        params["projection"] = json.dumps({
            "_id": 1,
            "text": 1
        })
        doc_map = {}
        while True:
            items, query = self.get_items("documents", params=params)
            for d in items:
                doc_map[d['_id']] = d['text']
            if query is None:
                break
        return doc_map

    def get_documents(self, collection_id: str) -> dict:
        # get documents
        params = {
            "where": json.dumps({
                "overlap": 0,
                "collection_id": collection_id
            })
        }
        return self._get_documents_map(params)

    def get_documents_by_id(self, document_ids: typing.List[str]):
        if len(document_ids) == 0:
            return {}
        params = {
            "where": json.dumps({
                "_id": {"$in": document_ids}
            })
        }
        return self._get_documents_map(params)

    def get_docs_with_annotations(self, collection_id, doc_map):
        doc_ids = list()
        documents = []
        ann_ids = list()
        labels = []

        #get annotations and make data
        query = 'annotations?where={"collection_id":"%s"}' % (collection_id)

        while True:
            items, query = self.get_items(query)

            for a in items:
                docid = a['document_id']
                # remove overlaps
                if docid not in doc_map:
                    continue
                doc_ids.append(docid)
                documents.append(doc_map[docid])
                ann_ids.append(a["_id"])
                labels.append(a["annotation"])

            if query is None:
                break

        return documents, labels, doc_ids, ann_ids

    def update(self, resource, id, etag, update_obj):
        headers = {'Content-Type': 'application/json', 'If-Match': etag}
        r = requests.patch('http://%s/%s/%s' % (self.entry_point, resource, id),
                           json.dumps(update_obj),headers=headers)
        if r.status_code != 200:
            return False
        return True


