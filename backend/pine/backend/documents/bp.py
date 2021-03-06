# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import json
import random

from flask import abort, Blueprint, jsonify, request
from werkzeug import exceptions

from .. import auth, collections, log
from ..data import service

bp = Blueprint("documents", __name__, url_prefix = "/documents")

def _document_user_can_projection():
    return service.params({"projection": {
        "collection_id": 1
    }})

def get_collection_ids_for(document_ids) -> set:
    if isinstance(document_ids, str):
        document_ids = [document_ids]
    # ideally we would use some "unique" or "distinct" feature here but eve doesn't seem to have it
    return set(item["collection_id"] for item in service.get_items("documents", params=service.params({
        "where": {
            "_id": {"$in": list(document_ids)}
        }, "projection": {
            "collection_id": 1
        }
    }))) 

def user_can_annotate(document):
    return collections.user_can_annotate_by_id(document["collection_id"])

def user_can_view(document):
    return collections.user_can_view_by_id(document["collection_id"])

def user_can_modify_metadata(document):
    return collections.user_can_modify_document_metadata_by_id(document["collection_id"])

def user_can_annotate_by_id(document_id):
    document = service.get_item_by_id("documents", document_id, params=_document_user_can_projection())
    return user_can_annotate(document)

def user_can_annotate_by_ids(document_ids):
    return collections.user_can_annotate_by_ids(get_collection_ids_for(document_ids))

def user_can_view_by_id(document_id):
    document = service.get_item_by_id("documents", document_id, params=_document_user_can_projection())
    return user_can_view(document)

def user_can_modify_metadata_by_id(document_id):
    document = service.get_item_by_id("documents", document_id, params=_document_user_can_projection())
    return user_can_modify_metadata(document)


@bp.route("/by_id/<doc_id>", methods = ["GET"])
@auth.login_required
def get_document(doc_id):
    resp = service.get("documents/" + doc_id)
    if not resp.ok:
        abort(resp.status_code)
    document = resp.json()
    if user_can_view(document):
        log.access_flask_view_document(document)
        return service.convert_response(resp)
    else:
        raise exceptions.Unauthorized()

@bp.route("/by_collection_id/<col_id>", defaults = {"page": "all"}, methods = ["GET"])
@bp.route("/by_collection_id/<col_id>/<page>", methods = ["GET"])
@auth.login_required
def get_documents_in_collection(col_id, page):
    truncate = json.loads(request.args.get("truncate", "true"))
    truncate_length = json.loads(request.args.get("truncateLength", "50"))
    collection = service.get_item_by_id("collections", col_id)
    if not collections.user_can_view(collection):
        raise exceptions.Unauthorized()
    params = service.where_params({
        "collection_id": col_id
    })
    if truncate:
        if truncate_length == 0:
            params["projection"] = json.dumps({
                "metadata": 0,
                "text": 0
            })
        else:
            params["projection"] = json.dumps({
                "metadata": 0
            })
            params["truncate"] = truncate_length

    if page == "all":
        return jsonify(service.get_all_using_pagination("documents", params))

    if page: params["page"] = page
    resp = service.get("documents", params = params)
    if not resp.ok:
        abort(resp.status_code, resp.content)
    data = resp.json()
    if truncate and truncate_length != 0:
        for document in data["_items"]:
            document["text"] = document["text"][0:truncate_length]
    return jsonify(data)

def _check_documents(documents) -> dict:
    collection_ids = set()
    for document in documents:
        if not isinstance(document, dict) or "collection_id" not in document or not document["collection_id"]:
            raise exceptions.BadRequest()
        collection_ids.add(document["collection_id"])
    collections_by_id = {}
    for collection_id in collection_ids:
        collection = service.get_item_by_id("collections", collection_id, params=service.params({
            "projection": {
                "creator_id": 1,
                "annotators": 1,
                "viewers": 1
            }
        }))
        if not collections.user_can_add_documents_or_images(collection):
            raise exceptions.Unauthorized()
        collections_by_id[collection_id] = collection
    return collections_by_id

@bp.route("/", strict_slashes = False, methods = ["POST"])
@auth.login_required
def add_document():
    docs = request.get_json()
    if not docs or (not isinstance(docs, dict) and not isinstance(docs, list) and not isinstance(docs, tuple)):
        raise exceptions.BadRequest()
    collections_by_id = _check_documents(docs if isinstance(docs, list) else [docs])

    # Get overlap information stored in related classifier db object, and assign overlap for added document
    collection_classifiers = {}
    for doc in (docs if isinstance(docs, list) else [docs]):
        # get classifier overlaps
        if doc["collection_id"] not in collection_classifiers:
            params = service.params({
                "where": {
                    "collection_id": doc["collection_id"]
                }, "projection": {
                    "overlap": 1
                }
            })
            resp = service.get("classifiers", params=params)
            if not resp.ok:
                abort(resp.status_code)
            classifier_obj = resp.json()["_items"]
            if len(classifier_obj) != 1:
                raise exceptions.BadRequest()
            collection_classifiers[doc["collection_id"]] = classifier_obj[0]

        classifier = collection_classifiers[doc["collection_id"]]
        overlap = classifier["overlap"]
        doc["overlap"] = 1 if random.random() < overlap else 0

        # initialize has_annotated dict
        if "has_annotated" not in doc:
            doc["has_annotated"] = {user_id: False for user_id in collections_by_id[doc["collection_id"]]["annotators"]}

    # Add document(s) to database
    doc_resp = service.post("documents", json=docs)
    if doc_resp.ok:
        if isinstance(docs, dict):
            log.access_flask_add_document(doc_resp.json())
        else:
            log.access_flask_add_documents(doc_resp.json()["_items"])
    else:
        abort(doc_resp.status_code)

    if isinstance(docs, dict):
        docs = [docs]
        doc_ids = [doc_resp.json()["_id"]]
    else:
        doc_ids = [d["_id"] for d in doc_resp.json()["_items"]]
    
    # Update next instances for added documents
    classifier_next_instances = {}
    for (i, document) in enumerate(docs):
        doc_id = doc_ids[i]

        classifier = collection_classifiers[document["collection_id"]]
        classifier_id = classifier["_id"]
        
        if classifier_id not in classifier_next_instances:
            # Get next_instances to which we'll add document
            next_instances_params = service.params({
                "where": {
                    "classifier_id": classifier_id
                }, "projection": {
                    "overlap_document_ids": 1,
                    "document_ids": 1
                }
            })
            resp = service.get("next_instances", params=next_instances_params)
            if not resp.ok:
                abort(resp.status_code)
            next_instances_obj = resp.json()["_items"]
            if len(next_instances_obj) != 1:
                raise exceptions.BadRequest()
            classifier_next_instances[classifier_id] = next_instances_obj[0]

        next_instances = classifier_next_instances[classifier_id]

        if document["overlap"] == 1:
            # Add document to overlap IDs for each annotator if it's an overlap document
            for annotator in next_instances["overlap_document_ids"]:
                next_instances["overlap_document_ids"][annotator].append(doc_id)
        else:
            # Add document to document_ids if it's not an overlap document
            next_instances["document_ids"].append(doc_id)

    # Patch next_instances with new documents
    for next_instances in classifier_next_instances.values():
        headers = {"If-Match": next_instances["_etag"]}
        service.remove_nonupdatable_fields(next_instances)
        resp = service.patch(["next_instances", next_instances["_id"]], json=next_instances, headers=headers)
        if not resp.ok:
            raise exceptions.BadRequest()

    return service.convert_response(doc_resp)

@bp.route("/can_annotate/<doc_id>", methods = ["GET"])
@auth.login_required
def can_annotate_document(doc_id):
    return jsonify(user_can_annotate_by_id(doc_id))

@bp.route("/can_modify_metadata/<doc_id>", methods = ["GET"])
@auth.login_required
def can_modify_metadata(doc_id):
    return jsonify(user_can_modify_metadata_by_id(doc_id))

@bp.route("/metadata/<doc_id>", methods = ["PUT"])
def update_metadata(doc_id):
    metadata = request.get_json()
    if not metadata:
        raise exceptions.BadRequest("Missing body JSON.")

    # get document
    document = service.get_item_by_id("documents", doc_id, params={
        "projection": json.dumps({
            "metadata": 1,
            "collection_id": 1
        })
    })
    if not user_can_modify_metadata(document):
        raise exceptions.Unauthorized()

    # update document
    if "metadata" in document:
        document["metadata"].update(metadata)
    else:
        document["metadata"] = metadata

    headers = {"If-Match": document["_etag"]}
    service.remove_nonupdatable_fields(document)
    return service.convert_response(
        service.patch(["documents", doc_id], json = document, headers = headers))

def init_app(app):
    app.register_blueprint(bp)
