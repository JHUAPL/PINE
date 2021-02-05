# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import json
import logging

from flask import abort, Blueprint, jsonify, request
from werkzeug import exceptions

from .. import auth, collections, log
from ..data import service
from ..documents import bp as documents

"""This module contains the api methods required to perform and display annotations in the front-end and store the 
annotations in the backend"""

logger = logging.getLogger(__name__)

CONFIG_ALLOW_OVERLAPPING_NER_ANNOTATIONS = "allow_overlapping_ner_annotations"

bp = Blueprint("annotations", __name__, url_prefix = "/annotations")

def check_document_by_id(doc_id: str):
    """
    Verify that a document with the given doc_id exists and that the logged in user has permissions to access the
    document
    :param doc_id: str
    :return: dict
    """
    if not documents.user_can_view_by_id(doc_id):
        raise exceptions.Unauthorized()

def check_document(doc: dict):
    if not documents.user_can_view(doc):
        raise exceptions.Unauthorized()

@bp.route("/mine/by_document_id/<doc_id>")
@auth.login_required
def get_my_annotations_for_document(doc_id):
    """
    Get the list of annotations (key, start_index, end_index) produced by the logged in user for the document matching
    the provided doc_id.
    :param doc_id: str
    :return: Response
    """
    check_document_by_id(doc_id)
    where = {
        "document_id": doc_id,
        "creator_id": auth.get_logged_in_user()["id"]
    }
    resp = service.get("annotations", params = service.where_params(where))
    if not resp.ok:
        abort(resp.status_code)
    return service.convert_response(resp)

@bp.route("/others/by_document_id/<doc_id>")
@auth.login_required
def get_others_annotations_for_document(doc_id):
    """
    Get the list of annotations (key, start_index, end_index) produced by all other users, not including the logged in
    user for the document matching the provided doc_id.
    :param doc_id: str
    :return: str
    """
    check_document_by_id(doc_id)
    where = {
        "document_id": doc_id,
        # $eq doesn't work here for some reason -- maybe because objectid?
        "creator_id": { "$not": { "$in": [auth.get_logged_in_user()["id"]] } }
    }
    resp = service.get("annotations", params = service.where_params(where))
    if not resp.ok:
        abort(resp.status_code)
    return service.convert_response(resp)

@bp.route("/by_document_id/<doc_id>")
@auth.login_required
def get_annotations_for_document(doc_id):
    """
    Get the list of annotations (key, start_index, end_index) produced by all users for the document matching the
    provided doc_id.
    :param doc_id: str
    :return: str
    """
    check_document_by_id(doc_id)
    where = {
        "document_id": doc_id
    }
    resp = service.get("annotations", params = service.where_params(where))
    if not resp.ok:
        abort(resp.status_code)
    return service.convert_response(resp)

def get_current_annotation(doc_id, user_id):
    """
    Get all annotations of the provided document created by the given user.
    :param doc_id: str
    :param user_id: str
    :return: List
    """
    where = {
        "document_id": doc_id,
        "creator_id": user_id
    }
    annotations = service.get_all_items("/annotations", params=service.where_params(where))
    if len(annotations) > 0:
        return annotations[0]
    else:
        return None

# def is_ner_annotation(ann):
#     """
#     Verify that the provided annotation is in the valid format for an NER Annotation
#     :param ann: Any
#     :return: Bool
#     """
#     return (type(ann) is list or type(ann) is tuple) and len(ann) == 3

def check_overlapping_annotations(collection, ner_annotations):
    # if allow_overlapping_ner_annotations is false, check them
    if "configuration" in collection and CONFIG_ALLOW_OVERLAPPING_NER_ANNOTATIONS in collection["configuration"] and not collection["configuration"][CONFIG_ALLOW_OVERLAPPING_NER_ANNOTATIONS]:
        for idx, val in enumerate(ner_annotations):
            if idx == 0: continue
            prev = ner_annotations[idx - 1]
            if val[0] < prev[1]:
                raise exceptions.BadRequest("Collection is configured not to allow overlapping annotations")

# @bp.route("/mine/by_document_id/<doc_id>/ner", methods = ["POST", "PUT"])
# @auth.login_required
# def save_ner_annotations(doc_id):
#     """
#     Save new NER annotations to the database as an entry for the logged in user, for the document. If there are already
#     annotations, use a patch request to update with the new annotations. If there are not, use a post request to create
#     a new entry.
#     :param doc_id: str
#     :return: str
#     """
#     if not request.is_json:
#         raise exceptions.BadRequest()
#     check_document_by_id(doc_id)
#     document = service.get_item_by_id("documents", doc_id, {
#         "projection": json.dumps({
#             "collection_id": 1,
#             "metadata": 1
#         })
#     })
#     annotations = request.get_json()
#     user_id = auth.get_logged_in_user()["id"]
#     annotations = [(ann["start"], ann["end"], ann["label"]) for ann in annotations]
#     check_overlapping_annotations(document, annotations) 
#     new_annotation = {
#         "creator_id": user_id,
#         "collection_id": document["collection_id"],
#         "document_id": doc_id,
#         "annotation": annotations
#     }
#     
#     current_annotation = get_current_annotation(doc_id, user_id)
#     if current_annotation != None:
#         if current_annotation["annotation"] == annotations:
#             return jsonify(True)
#         headers = {"If-Match": current_annotation["_etag"]}
#         
#         # add all the other non-ner labels
#         for annotation in current_annotation["annotation"]:
#             if not is_ner_annotation(annotation):
#                 new_annotation["annotation"].append(annotation)
# 
#         resp = service.patch(["annotations", current_annotation["_id"]], json = new_annotation, headers = headers)
#     else:
#         resp = service.post("annotations", json = new_annotation)
#     
#     if resp.ok:
#         new_annotation["_id"] = resp.json()["_id"]
#         log.access_flask_annotate_document(document, new_annotation)
#         
#     return jsonify(resp.ok)

# def is_doc_annotation(ann):
#     """
#     Verify that an annotation has the correct format (string)
#     :param ann: Any
#     :return: Bool
#     """
#     return isinstance(ann, str)

# @bp.route("/mine/by_document_id/<doc_id>/doc", methods = ["POST", "PUT"])
# @auth.login_required
# def save_doc_labels(doc_id):
#     """
#     Save new labels to the database as an entry for the logged in user, for the document. If there are already
#     annotations/labels, use a patch request to update with the new labels. If there are not, use a post request to
#     create a new entry.
#     :param doc_id:
#     :return:
#     """
#     if not request.is_json:
#         raise exceptions.BadRequest()
#     check_document_by_id(doc_id)
#     document = service.get_item_by_id("documents", doc_id, {
#         "projection": json.dumps({
#             "collection_id": 1,
#             "metadata": 1
#         })
#     })
#     
#     labels = request.get_json()
#     user_id = auth.get_logged_in_user()["id"]
#     new_annotation = {
#         "creator_id": user_id,
#         "collection_id": document["collection_id"],
#         "document_id": doc_id,
#         "annotation": labels
#     }
#     
#     current_annotation = get_current_annotation(doc_id, user_id)
#     if current_annotation != None:
#         if current_annotation["annotation"] == labels:
#             return jsonify(True)
#         headers = {"If-Match": current_annotation["_etag"]}
#         
#         # add all the other non-doc labels
#         for annotation in current_annotation["annotation"]:
#             if not is_doc_annotation(annotation):
#                 new_annotation["annotation"].append(annotation)
#         
#         resp = service.patch(["annotations", current_annotation["_id"]], json = new_annotation, headers = headers)
#     else:
#         resp = service.post("annotations", json = new_annotation)
# 
#     if resp.ok:
#         new_annotation = resp.json()["_id"]
#         log.access_flask_annotate_document(document, new_annotation)
#         
#     return jsonify(resp.ok)


def set_document_to_annotated_by_user(doc_id, user_id):
    """
    Modify the parameter in the database for the document signifying that the given user has annotated the given
    document
    :param doc_id: str
    :param user_id: str
    :return: whether the update succeeded
    :rtype: bool
    """
    document = service.get_item_by_id("/documents", doc_id, params={
        "projection": json.dumps({
            "has_annotated": 1
        })
    })
    if "has_annotated" in document and user_id in document["has_annotated"] and document["has_annotated"][user_id]:
        return True
    new_document = {
        "has_annotated": document["has_annotated"] if "has_annotated" in document else {}
    }
    new_document["has_annotated"][user_id] = True
    headers = {"If-Match": document["_etag"]}
    return service.patch(["documents", doc_id], json=new_document, headers=headers).ok

def _make_annotations(body):
    if not isinstance(body, dict) or "doc" not in body or "ner" not in body:
        raise exceptions.BadRequest()
    if (not isinstance(body["doc"], list) and not isinstance(body["doc"], tuple)) or \
       (not isinstance(body["ner"], list) and not isinstance(body["ner"], tuple)):
        raise exceptions.BadRequest()

    doc_labels = body["doc"]
    for ann in doc_labels:
        if not isinstance(ann, str) or len(ann.strip()) == 0:
            raise exceptions.BadRequest()

    ner_annotations = body["ner"]
    for (i, ann) in enumerate(ner_annotations):
        if isinstance(ann, dict):
            if "start" not in ann or "end" not in ann or "label" not in ann:
                raise exceptions.BadRequest()
            if not isinstance(ann["start"], int) or not isinstance(ann["end"], int) or \
               not isinstance(ann["label"], str) or len(ann["label"].strip()) == 0:
                raise exceptions.BadRequest()
            ner_annotations[i] = (ann["start"], ann["end"], ann["label"])
        elif isinstance(ann, list) or isinstance(ann, tuple):
            if len(ann) != 3 or not isinstance(ann[0], int) or not isinstance(ann[1], int) or \
               not isinstance(ann[2], str) or len(ann[2].strip()) == 0:
                raise exceptions.BadRequest()
        else:
            raise exceptions.BadRequest()
    ner_annotations.sort(key = lambda x: x[0])

    return (doc_labels, ner_annotations)

def _add_or_update_annotation(new_annotation):
    doc_id = new_annotation["document_id"]
    user_id = new_annotation["creator_id"]
    current_annotation = get_current_annotation(doc_id, user_id)
    success = False
    if current_annotation != None:
        new_annotation["_id"] = current_annotation["_id"]
        if current_annotation["annotation"] == new_annotation["annotation"]:
            return new_annotation["_id"]
        else:
            headers = {"If-Match": current_annotation["_etag"]}
            resp = service.patch(["annotations", current_annotation["_id"]], json = new_annotation, headers = headers)
    else:
        updated_annotated_field = set_document_to_annotated_by_user(doc_id, user_id)
        resp = service.post("annotations", json = new_annotation)
        success = resp.ok and updated_annotated_field
        new_annotation["_id"] = resp.json()["_id"]
    
    if success:
        log.access_flask_annotate_document(new_annotation)

    return new_annotation["_id"]

@bp.route("/mine/by_document_id/<doc_id>", methods = ["POST", "PUT"])
def save_annotations(doc_id):
    """
    Save new NER annotations and labels to the database as an entry for the logged in user, for the document. If there
    are already annotations, use a patch request to update with the new annotations. If there are not, use a post
    request to create a new entry.
    :param doc_id: str
    :return: bool
    """
    # If you change input or output, update client modules pine.client.models and pine.client.client
    if not request.is_json:
        raise exceptions.BadRequest()

    document = service.get_item_by_id("documents", doc_id, params=service.params({
        "projection": {
            "collection_id": 1,
            "metadata": 1
        }
    }))
    check_document(document)

    body = request.get_json()
    (doc_labels, ner_annotations) = _make_annotations(body)

    collection = service.get_item_by_id("collections", document["collection_id"], params=service.params({
        "projection": {
            "configuration": 1
        }
    }))
    check_overlapping_annotations(collection, ner_annotations)
    
    user_id = auth.get_logged_in_user()["id"]
    new_annotation = {
        "creator_id": user_id,
        "collection_id": document["collection_id"],
        "document_id": doc_id,
        "annotation": doc_labels + ner_annotations
    }

    return jsonify(_add_or_update_annotation(new_annotation))

@bp.route("/mine/by_collection_id/<collection_id>", methods = ["POST", "PUT"])
def save_collection_annotations(collection_id: str):
    # If you change input or output, update client modules pine.client.models and pine.client.client
    collection = service.get_item_by_id("collections", collection_id, params=service.params({
        "projection": {
            "configuration": 1,
            "creator_id": 1,
            "viewer": 1,
            "annotators": 1
        }
    }))
    if not collections.user_can_annotate(collection):
        raise exceptions.Unauthorized()

    if not request.is_json:
        raise exceptions.BadRequest()
    doc_annotations = request.get_json()
    if not isinstance(doc_annotations, dict):
        raise exceptions.BadRequest()
    
    skip_document_updates = json.loads(request.args.get("skip_document_updates", "false"))
    
    # make sure all the documents actually belong to that collection
    collection_ids = list(documents.get_collection_ids_for(doc_annotations.keys()))
    if len(collection_ids) != 1 or collection_ids[0] != collection_id:
        raise exceptions.Unauthorized()
    user_id = auth.get_logged_in_user()["id"]

    # first try batch mode
    new_annotations = []
    for (doc_id, body) in doc_annotations.items():
        (doc_labels, ner_annotations) = _make_annotations(body)
        check_overlapping_annotations(collection, ner_annotations)
        new_annotations.append({
            "creator_id": user_id,
            "collection_id": collection_id,
            "document_id": doc_id,
            "annotation": doc_labels + ner_annotations
        })
    resp = service.post("annotations", json=new_annotations)
    if resp.ok:
        for (i, created_annotation) in enumerate(resp.json()["_items"]):
            new_annotations[i]["_id"] = created_annotation["_id"]
            if not skip_document_updates:
                set_document_to_annotated_by_user(new_annotations[i]["document_id"],
                                                  new_annotations[i]["creator_id"])
        log.access_flask_annotate_documents(new_annotations)
        return jsonify([annotation["_id"] for annotation in new_annotations])

    # fall back on individual mode
    added_ids = []
    for annotation in new_annotations:
        added_id = _add_or_update_annotation(annotation["document_id"], user_id, annotation)
        if added_id:
            added_ids.append(added_id)
    return jsonify(added_ids)

def init_app(app):
    app.register_blueprint(bp)
