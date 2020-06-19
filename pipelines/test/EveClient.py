# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import os
import json
import requests
import pydash


def get_headers():
    return {'Content-Type': 'application/json'}


# TODO: get environment variable to set eve host
def create_url(path, *additional_paths):
    return "/".join(["http://localhost:5001", path.lstrip("/")] + list(additional_paths))


def get_annotations_in_document(doc_id):
    url = create_url("annotations")
    where = {"document_id": doc_id}
    resp = requests.get(url, params={"where": json.dumps(where)}).json()
    annotations = pydash.get(resp, '_items', None)
    return annotations


def parse_annotations_into_array(annotations):
    parseAnnotations=[]
    for annotation in annotations:
        parseAnnotations.append(annotation["annotation"])
    return parseAnnotations
# Previous fix:
#     for annotation in annotations:
#         annotation_tuple_list = []
#         for a in pydash.get(annotation, 'annotation', None):
#             annotation_tuple_list.append(tuple(a))
#     return annotation_tuple_list


def get_documents_in_collection(col_id):
    url = create_url("documents")
    where = {"collection_id": col_id}
    resp = requests.get(url, params={"where": json.dumps(where)}).json()
    documents = pydash.get(resp, '_items', None)
    return documents


def get_documents_text_with_annotation(collection_id):
    documents = get_documents_in_collection(collection_id)
    documents_text = []
    annotations = []
    for document in documents:
        annotation_items = get_annotations_in_document(document["_id"])
        annotations.append(parse_annotations_into_array(annotation_items))
        documents_text.append(document["text"])

    return documents_text, annotations


def get_collections():
    url = create_url("collections")
    resp = requests.get(url).json()
    collections = pydash.get(resp, '_items', None)
    return collections


def add_classifier(collection_id, overlap, pipeline_id, parameters, labels, filename):
    url = create_url("classifiers")
    classifier = {
        "collection_id": collection_id,
        "overlap": overlap,
        "pipeline_id": pipeline_id,
        "parameters": dict(parameters),
        "labels": list(labels),
        "filename": filename
    }
    resp = requests.post(url, json.dumps(classifier), headers=get_headers())

    print(resp.content)
    return resp


def add_metrics(collection_id, classifier_id, documents, annotations, folds, metrics):
    url = create_url("metrics")
    metric = {
        "collection_id": collection_id,
        "classifier_id": classifier_id,
        "documents": documents,
        "annotations": annotations,
        "folds": folds,
        "metrics": metrics
    }
    resp = requests.post(url, json.dumps(metric), headers=get_headers())
    return resp
