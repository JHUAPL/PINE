#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import csv
import json
import logging
import os
import random
import sys
import typing

from sklearn.datasets import fetch_20newsgroups

DIR = os.path.dirname(os.path.realpath(__file__))

CLIENT_PYTHON_DIR = os.path.realpath(os.path.join(DIR, "..", "..", "client"))

USERS_FILE = os.path.join(DIR, "users.json")
PIPELINES_FILE = os.path.join(DIR, "pipelines.json")
COLLECTIONS_FILE = os.path.join(DIR, "collections.json")

BACKEND_PORT = int(os.environ.get("BACKEND_PORT", 5000))
EVE_PORT = int(os.environ.get("EVE_PORT", 5001))
MONGO_PORT = int(os.environ.get("MONGO_PORT", 27018))

class TestDataImporter(object):

    def __init__(self, backend_base_uri: str, eve_base_uri: str, mongodb_base_uri: str):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.base_uris = [backend_base_uri, eve_base_uri, mongodb_base_uri]
        self.client = pine.client.LocalPineClient(*self.base_uris)
        if not self.client.is_valid():
            raise Exception("Cannot connect to PINE backend/eve/mongodb.")
        self.added_users = []
        self.user_clients = {}
        self.added_pipelines = []
        self.added_collections = []
        self.added_collection_document_ids = {}

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.client.logout()
        for client in self.user_clients.values():
            client.logout()

    def drop_databases(self):
        self.client.eve.mongo.drop_database("test") # old database
        self.client.eve.mongo.drop_database(self.client.eve.mongo_db.name)
        self.logger.info("Dropped databases: {}".format(["test", self.client.eve.mongo_db.name]))

    def _update_ids(self, objs, obj_ids):
        if len(obj_ids) != len(objs):
            raise Exception("Problem adding items: number of returned IDs is not correct.")
        for (i, obj) in enumerate(objs):
            obj["_id"] = obj_ids[i]

    def add_users_from(self, user_filename: str, login_clients=True) -> typing.List[dict]:
        with open(user_filename, "r") as f:
            users = json.load(f)
        user_ids = self.client.eve.add_users(users)
        self._update_ids(users, user_ids)
        self.added_users += users

        self.logger.info("Added {} users".format(len(users)))
        for user in users:
            self.logger.info("\t{} ({})".format(user["_id"], user["email"]))

        if login_clients:
            for user in users:
                client = pine.client.LocalPineClient(*self.base_uris)
                self.user_clients[user["_id"]] = client
                client.login_eve(user["email"], user["password"] if "password" in user else user["email"])
                self.logger.info("Logged in as {}".format(user["email"]))

        return users

    def add_pipelines_from(self, pipelines_filename: str) -> typing.List[dict]:
        with open(pipelines_filename, "r") as f:
            pipelines = json.load(f)
        pipeline_ids = self.client.eve.add_pipelines(pipelines)
        self._update_ids(pipelines, pipeline_ids)
        self.added_pipelines += pipelines
        
        self.logger.info("Added {} pipelines".format(len(pipelines)))
        for pipeline in pipelines:
            self.logger.info("\t{} ({})".format(pipeline["_id"], pipeline["title"]))
        
        return pipelines

    def add_collections_from(self, collections_filename: str) -> typing.List[dict]:
        with open(collections_filename, "r") as f:
            collections = json.load(f)

        return [self.add_collection(c) for c in collections]

    def add_collection(self, collection_data) -> dict:
        collection = collection_data["collection"]
        classifier = collection_data["classifier"]
        documents = collection_data["documents"] if "documents" in collection_data else None

        user_id = collection["creator_id"]
        if user_id not in self.user_clients:
            raise Exception("User {} does not have a logged in client.".format(user_id))
        client = self.user_clients[user_id]

        # add a CSV file for documents if specified
        collection_builder = client.collection_builder(collection=collection, **classifier)
        if documents and "csv_file" in documents:
            if "csv_filename" in documents["csv_file"] and not os.path.isabs(documents["csv_file"]["csv_filename"]):
                documents["csv_file"]["csv_filename"] = os.path.realpath(os.path.join(DIR, documents["csv_file"]["csv_filename"]))
            collection_builder.document_csv_file(**documents["csv_file"])

        collection_id = client.create_collection(collection_builder)
        collection["_id"] = collection_id
        self.added_collections.append(collection)
        if not collection_id in self.added_collection_document_ids:
            self.added_collection_document_ids[collection_id] = []
        self.logger.info("Created collection {} ({}) for {}".format(collection_id, collection["metadata"]["title"], collection["creator_id"]))

        docs = []
        doc_annotations = []
        if documents and "csv_file" in documents:
            doc_ids = [doc["_id"] for doc in client.get_collection_documents(collection_id, True, 0)]
            self.added_collection_document_ids[collection_id] = doc_ids
            self.logger.info("\tAdded {} documents created by {}".format(len(doc_ids), collection["creator_id"]))
        else:
            (docs, doc_annotations) = self._make_collection_documents_and_annotations(collection, documents)

        if docs:
            for (i, doc) in enumerate(docs):
                doc["has_annotated"] = {user_id: False for user_id in collection["annotators"]}
                if doc_annotations and doc_annotations[i]:
                    doc["has_annotated"][doc_annotations[i]["creator_id"]] = True
            skip_document_updates=True

            doc_ids = client.add_documents(docs)
            self._update_ids(docs, doc_ids)
            self.added_collection_document_ids[collection_id] += doc_ids
            self.logger.info("\tAdded {} documents created by {}".format(len(doc_ids), collection["creator_id"]))

            if doc_annotations:
                # create a map of which document annotations will be added by which user
                user_annotations = {user_id: {} for user_id in collection["annotators"]}
                for (i, doc_annotation) in enumerate(doc_annotations):
                    if not doc_annotation:
                        continue
                    creator_id = doc_annotation["creator_id"]
                    del doc_annotation["creator_id"]
                    user_annotations[creator_id][doc_ids[i]] = doc_annotation

                annotation_ids = []
                for user_id in user_annotations:
                    if user_annotations[user_id]:
                        added_annotation_ids = client.annotate_collection_documents(collection_id, user_annotations[user_id],skip_document_updates=skip_document_updates)
                        self.logger.info("\tAdded {} annotations created by {}".format(len(added_annotation_ids), user_id))
                        annotation_ids += added_annotation_ids

        self.added_collection_document_ids[collection_id] = doc_ids

        return collection

    def _make_collection_documents_and_annotations(self, collection, documents):
        doc_texts = []
        doc_annotations = []
        doc_overlap = 0
        if documents:
            num_docs = documents["num_docs"] if "num_docs" in documents else None
            if "overlap" in documents:
                doc_overlap = documents["overlap"]

            if "fetch_20newsgroups" in documents:
                # fetch data
                data = fetch_20newsgroups(**documents["fetch_20newsgroups"])
                if documents["fetch_20newsgroups"]["categories"] != collection["labels"]:
                    raise Exception("Categories ({}) do not match collection labels ({}).".format(
                        documents["fetch_20newsgroups"]["categories"], collection["labels"]))
                if num_docs == None:
                    num_docs = len(data.data)

                # get document/annotation info
                doc_texts = [data.data[i] for i in range(num_docs)]
                start = max(0, num_docs - documents["num_annotations"] if "num_annotations" in documents else 0)
                doc_annotations = [{
                    "doc": [documents["fetch_20newsgroups"]["categories"][data.target[i]]],
                    "ner": []
                } if i >= start else None for i in range(num_docs)]

            elif "ner_annotations" in documents:
                # fetch data
                [doc_texts, annotations, label_stats] = load_nlp_annotations(**{
                    **documents["ner_annotations"],
                    **{
                        "num_docs": num_docs
                    }})
                if list(label_stats.keys()) != collection["labels"]:
                    raise Exception("Parsed labels ({}) do not match collection labels ({}).".format(
                        list(label_stats.keys()), collection["labels"]))

                # get annotation info
                doc_annotations = [{
                    "doc": [],
                    "ner": ann
                } for ann in annotations]

        docs = []
        if doc_texts:
            user_id = collection["creator_id"]
            collection_id = collection["_id"]
            docs = [{
                "creator_id": user_id,
                "collection_id": collection_id,
                "overlap": doc_overlap,
                "text": doc_texts[i]
            } for i in range(len(doc_texts))]

            if "random_images" in documents:
                images = documents["random_images"]
                num_images = len(images)
                for doc in docs:
                    doc["metadata"] = {"imageUrl": images[random.randrange(0, num_images)]}

        if len(docs) != len(doc_annotations):
            raise Exception("Number of documents and annotations don't match.")

        random_annotators = "random_annotators" in documents and documents["random_annotators"]
        for doc_annotation in doc_annotations:
            if not doc_annotation:
                continue
            if random_annotators:
                doc_annotation["creator_id"] = random.choice(collection["annotators"])
            else:
                doc_annotation["creator_id"] = collection["creator_id"]

        return (docs, doc_annotations)

def load_nlp_annotations(csv_file, num_docs, sentences_per_doc = 10):
    if not os.path.isabs(csv_file):
        csv_file = os.path.realpath(os.path.join(DIR, csv_file))
    
    docs = []
    anns = []
    stats = {}
    with open(csv_file, 'r', encoding='utf-8', errors='ignore') as csv_file:
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
                   docs.append(doc_text)
                   doc_text = ''
                   anns.append(doc_anns)
                   doc_anns = []
                   if len(docs) > num_docs-2:
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
    sys.path.append(CLIENT_PYTHON_DIR)
    import pine.client
    pine.client.setup_logging()

    with TestDataImporter(backend_base_uri = "http://localhost:{}".format(BACKEND_PORT),
                          eve_base_uri = "http://localhost:{}".format(EVE_PORT),
                          mongodb_base_uri = "mongodb://localhost:{}".format(MONGO_PORT)) as importer:
        # clear out databases
        importer.drop_databases()

        # add users and pipelines
        importer.add_users_from(USERS_FILE, login_clients=True)
        importer.add_pipelines_from(PIPELINES_FILE)

        # generate collections
        importer.add_collections_from(COLLECTIONS_FILE)
