# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import requests
import json
import os

PAGINATION = False

if "FLASK_PORT" in os.environ:
    EVE_URL = 'http://localhost:{}/'.format(os.environ["FLASK_PORT"])
else:
    EVE_URL = 'http://localhost:5001/'

def get_collection_annotators(collection_id):
    collection = requests.get(EVE_URL + 'collections/' + collection_id).json()
    return collection["annotators"]

def get_document_annotations(doc_id):
    annotations = requests.get(EVE_URL + 'annotations', params = {"where" : json.dumps({"document_id" : doc_id })}).json()["_items"]
    return (annotations)

def update_document(document):
    if "has_annotated" not in document.keys():
        new_document = {"has_annotated": {} }
        annotators = get_collection_annotators(document["collection_id"])

        for annotator in annotators:
            new_document["has_annotated"][annotator] = False
        for annotation in get_document_annotations(document["_id"]):
            print(annotation["document_id"])
            new_document["has_annotated"][annotation["creator_id"]] = True
        e_tag = document["_etag"]
        headers = {"If-Match": e_tag}
        print(requests.patch(EVE_URL + "documents/" + document["_id"], json= new_document, headers = headers))

DOCUMENT_PROJECTION = {
    "projection": json.dumps({
        "text": 0
    })
}

if PAGINATION:
    page = 0
    documents = requests.get(EVE_URL + 'documents?page=' + str(page), params=DOCUMENT_PROJECTION).json()["_items"]
    while len(documents) > 0:
        page += 1
        documents = requests.get(EVE_URL + 'documents?page=' + str(page), params=DOCUMENT_PROJECTION).json()["_items"]

        for document in documents:
            update_document(document)

else:
    documents = requests.get(EVE_URL + "documents", params=DOCUMENT_PROJECTION).json()["_items"]
    for document in documents:
        update_document(document)

