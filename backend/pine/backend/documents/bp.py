# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import json
import random
import re
import typing

from flask import abort, Blueprint, jsonify, request
import lxml.html.clean
from werkzeug import exceptions

from .. import auth, collections, log, models
from ..data import service

bp = Blueprint("documents", __name__, url_prefix = "/documents")

HTML_CLEANER = lxml.html.clean.Cleaner(
    page_structure=True, # keep body only
    links=True, # remove <link> (not <a>)
    safe_attrs_only=True, # strip out non-standard attributes
    style=False, # leave <style>
    javascript=True, # no javascript!
    scripts=True, # no javascript!!
    meta=True, # strip out <meta>
    forms=True, # strip out forms
    embedded=True, # strip out embedded flash, etc.,
    kill_tags=["title"] # otherwise the title gets embedded at the top
)

def _document_user_can_projection():
    return service.params({"projection": {
        "collection_id": 1
    }})

def get_collection_ids_for(document_ids) -> typing.List[str]:
    if isinstance(document_ids, str):
        document_ids = [document_ids]
    # ideally we would use some "unique" or "distinct" feature here but eve doesn't seem to have it
    return list(set(item["collection_id"] for item in service.get_all_items("documents", params=service.params({
        "where": {
            "_id": {"$in": list(document_ids)}
        }, "projection": {
            "collection_id": 1
        }
    }))))

def get_user_permissions(document: dict) -> models.CollectionUserPermissions:
    return collections.get_user_permissions_by_id(document["collection_id"])

def get_user_permissions_by_id(document_id: str) -> models.CollectionUserPermissions:
    document = service.get_item_by_id("documents", document_id, params=_document_user_can_projection())
    return get_user_permissions(document)

def get_user_permissions_by_ids(document_ids: typing.Iterable[str]) -> typing.List[models.CollectionUserPermissions]:
    return collections.get_user_permissions_by_ids(get_collection_ids_for(document_ids))

def sanitize_document(document: dict):
    if document and "metadata" in document and "html_view" in document["metadata"]:
        document["metadata"]["html_view"] = HTML_CLEANER.clean_html(document["metadata"]["html_view"])

@bp.route("/by_id/<doc_id>", methods = ["GET"])
@auth.login_required
def get_document(doc_id):
    resp = service.get("documents/" + doc_id)
    if not resp.ok:
        abort(resp.status_code)
    document = resp.json()
    if get_user_permissions(document).view:
        log.access_flask_view_document(document)
        return service.convert_response(resp)
    else:
        raise exceptions.Unauthorized()

@bp.route("/count_by_collection_id/<col_id>", methods = ["GET"])
@auth.login_required
def count_documents_in_collection(col_id):
    collection = service.get_item_by_id("collections", col_id)
    if not collections.get_user_permissions(collection).view:
        raise exceptions.Unauthorized()
    params = service.params({
        "where": {
            "collection_id": col_id
        },
        "projection": {
            "_id": 1
        },
        "max_results": 1
    })
    resp = service.get("documents", params=params)
    if not resp.ok:
        abort(resp.status_code)
    resp = resp.json()
    if "_meta" not in resp or resp["_meta"]["max_results"] != 1 or "total" not in resp["_meta"]:
        raise exceptions.InternalServerError("Pagination has not been turned on or correctly configured for documents.")
    return jsonify(resp["_meta"]["total"])

@bp.route("/by_collection_id_all/<col_id>", methods = ["GET"])
@auth.login_required
def get_all_documents_in_collection(col_id):
    truncate = json.loads(request.args.get("truncate", "true"))
    truncate_length = json.loads(request.args.get("truncateLength", "50"))
    collection = service.get_item_by_id("collections", col_id)
    if not collections.get_user_permissions(collection).view:
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

    return jsonify(service.get_all("documents", params=params))

@bp.route("/by_collection_id_paginated/<collection_id>", methods = ["GET"])
@auth.login_required
def get_paginated_documents_in_collection(collection_id):
    collection = service.get_item_by_id("collections", collection_id)
    if not collections.get_user_permissions(collection).view:
        raise exceptions.Unauthorized()

    if not "page" in request.args or not "pageSize" in request.args:
        raise exceptions.BadRequest("'page' and 'pageSize' must be provided.")

    page = json.loads(request.args.get("page"))
    if not isinstance(page, int):
        raise exceptions.BadRequest("'page' must be an integer.")
    # eve's pagination is 1-based
    page += 1

    page_size = json.loads(request.args.get("pageSize"))
    if not isinstance(page_size, int):
        raise exceptions.BadRequest("'pageSize' must be an integer.")

    sort = request.args.get("sort", None)
    if sort: sort = json.loads(sort)
    if sort and ("field" not in sort or "ascending" not in sort):
        raise exceptions.BadRequest("'sort' should have 'field' and 'ascending'.")

    filter_str = request.args.get("filter", None)
    if filter_str: filter_str = str(filter_str)

    truncate = json.loads(request.args.get("truncate", "true"))
    if not isinstance(truncate, bool):
        raise exceptions.BadRequest("'truncate' must be a boolean.")
    truncate_length = json.loads(request.args.get("truncateLength", "50"))
    if not isinstance(truncate_length, int):
        raise exceptions.BadRequest("'truncateLength' must be an integer.")

    params = {
        "where": {
            "collection_id": collection_id
        },
        "max_results": page_size,
        "page": page
    }
    if sort:
        params["sort"] = ("" if sort["ascending"] else "-") + sort["field"]
    if filter_str:
        params["where"] = {
            "$and": [
                params["where"],
                {
                    "text": {
                        "$regex": ".*{}.*".format(re.escape(filter_str))
                    }
                }
            ]
        }
    if truncate:
        params["projection"] = json.dumps({"metadata": 0})
        params["truncate"] = truncate_length

    return service.convert_response(service.get("documents", params=service.params(params)))

def _check_documents(documents) -> dict:
    collection_ids = set()
    for document in documents:
        if not isinstance(document, dict) or "collection_id" not in document or not document["collection_id"]:
            raise exceptions.BadRequest()
        collection_ids.add(document["collection_id"])
    collections_by_id = {}
    for collection_id in collection_ids:
        collection = service.get_item_by_id("collections", collection_id, params=service.params({
            "projection": collections.user_permissions_projection()
        }))
        if not collections.get_user_permissions(collection).add_documents:
            raise exceptions.Unauthorized()
        collections_by_id[collection_id] = collection
    return collections_by_id

def _get_collection_classifiers(collection_ids):
    collection_classifiers = {}
    for collection_id in collection_ids:
        if collection_id not in collection_classifiers:
            params = service.params({
                "where": {
                    "collection_id": collection_id
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
            collection_classifiers[collection_id] = classifier_obj[0]
    return collection_classifiers

def _get_classifier_next_instances(collection_classifiers: dict):
    # documents objects must have _id and collection_id
    classifier_next_instances = {}
    for collection_id in collection_classifiers:
        classifier = collection_classifiers[collection_id]
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
    return classifier_next_instances

@bp.route("/", strict_slashes = False, methods = ["POST"])
@auth.login_required
def add_document():
    docs = request.get_json()
    if not docs or (not isinstance(docs, dict) and not isinstance(docs, list) and not isinstance(docs, tuple)):
        raise exceptions.BadRequest()
    if not isinstance(docs, list):
        docs = [docs]
    for doc in docs:
        if not doc: # check for empty/null documents
            raise exceptions.BadRequest()
    collections_by_id = _check_documents(docs)

    # Get overlap information stored in related classifier db object, and assign overlap for added document
    collection_classifiers = _get_collection_classifiers([doc["collection_id"] for doc in docs])
    for doc in (docs if isinstance(docs, list) else [docs]):
        # get classifier overlaps
        classifier = collection_classifiers[doc["collection_id"]]
        overlap = classifier["overlap"]
        doc["overlap"] = 1 if random.random() < overlap else 0

        # initialize has_annotated dict
        if "has_annotated" not in doc:
            doc["has_annotated"] = {user_id: False for user_id in collections_by_id[doc["collection_id"]]["annotators"]}

        # sanitize
        sanitize_document(doc)

    # Add document(s) to database
    doc_resp = service.post("documents", json=docs)
    if not doc_resp.ok:
        abort(doc_resp.status_code)
    
    doc_resp_json = doc_resp.json()
    if "_items" in doc_resp_json:
        log.access_flask_add_documents(doc_resp_json["_items"])
        doc_ids = [d["_id"] for d in doc_resp_json["_items"]]
    else:
        log.access_flask_add_document(doc_resp_json)
        doc_ids = [doc_resp_json["_id"]]

    # Update next instances for added documents
    classifier_next_instances = _get_classifier_next_instances(collection_classifiers)
    for (i, document) in enumerate(docs):
        doc_id = doc_ids[i]

        classifier = collection_classifiers[document["collection_id"]]
        classifier_id = classifier["_id"]
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

@bp.route("/user_permissions/<doc_id>", methods = ["GET"])
@auth.login_required
def endpoint_get_user_permissions(doc_id):
    return jsonify(get_user_permissions_by_id(doc_id).to_dict())

@bp.route("/metadata/<doc_id>", methods = ["PUT"])
@auth.login_required
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
    if not get_user_permissions(document).modify_document_metadata:
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

def _delete_documents_by_id(doc_ids: typing.List[str]) -> bool:
    for perm in get_user_permissions_by_ids(doc_ids):
        if not perm.delete_documents:
            raise exceptions.Unauthorized()
    
    documents = []
    for doc_id in doc_ids:
        doc_resp = service.get(["documents", doc_id], params=service.params({
            "projection": {
                "_id": 1,
                "collection_id": 1
            }
        }))
        if not doc_resp.ok:
            abort(doc_resp.status_code)
        documents.append(doc_resp.json())

    changed_objects = {
        "next_instances": {
            "updated": []
        },
        "annotations": {
            "deleted": []
        },
        "documents": {
            "deleted": []
        }
    }
    
    # iaa_reports will get updated on the next annotation call
    # metrics will get updated on the next train call
    
    # next_instances
    collection_classifiers = _get_collection_classifiers([doc["collection_id"] for doc in documents])
    classifier_next_instances = _get_classifier_next_instances(collection_classifiers)
    for classifier_id in classifier_next_instances:
        next_instances = classifier_next_instances[classifier_id]
        
        original_overlap_count = sum([len([next_instances["overlap_document_ids"][ann] for ann in next_instances["overlap_document_ids"]])])
        for annotator in next_instances["overlap_document_ids"]:
            next_instances["overlap_document_ids"][annotator] = [doc_id for doc_id in next_instances["overlap_document_ids"][annotator] if doc_id not in doc_ids]
        modified_overlap_count = sum([len([next_instances["overlap_document_ids"][ann] for ann in next_instances["overlap_document_ids"]])])
        
        original_document_count = len(next_instances["document_ids"])
        next_instances["document_ids"] = [doc_id for doc_id in next_instances["document_ids"] if doc_id not in doc_ids]
        modified_document_count = len(next_instances["document_ids"])
    
        if original_overlap_count != modified_overlap_count or original_document_count != modified_document_count:
            next_instance_id = next_instances["_id"]
            headers = {"If-Match": next_instances["_etag"]}
            service.remove_nonupdatable_fields(next_instances)
            resp = service.patch(["next_instances", next_instance_id], json=next_instances, headers=headers)
            if resp.ok:
                changed_objects["next_instances"]["updated"].append(next_instance_id)
            else:
                raise exceptions.InternalServerError()
    
    # annotations
    for doc_id in doc_ids:
        annotations = service.get_all_items("annotations", params = service.params({
            "where": {
                "document_id": doc_id
            }, "projection": {
                "_id": 1
            }
        }))
        for annotation in annotations:
            annotation_id = annotation["_id"]
            headers = {"If-Match": annotation["_etag"]}
            service.remove_nonupdatable_fields(annotation)
            resp = service.delete(["annotations", annotation_id], headers=headers)
            if resp.ok:
                changed_objects["annotations"]["deleted"].append(annotation_id)
            else:
                raise exceptions.InternalServerError()
    
    # delete actual documents
    for doc in documents:
        doc_id = doc["_id"]
        headers = {"If-Match": doc["_etag"]}
        service.remove_nonupdatable_fields(doc)
        resp = service.delete(["documents", doc_id], headers=headers)
        if resp.ok:
            changed_objects["documents"]["deleted"].append(doc_id)
        else:
            raise exceptions.InternalServerError()
    
    return (True, changed_objects)

# note: this will not retrain any models that had used this document
# will not reduce classifiers.annotated_document_count
@bp.route("/by_id/<doc_id>", methods = ["DELETE"])
@auth.login_required
def delete_document(doc_id: str):
    (success, changed_objs) = _delete_documents_by_id([doc_id])
    return jsonify({
        "success": success,
        "changed_objs": changed_objs
    })

# note: this will not retrain any models that had used these documents
@bp.route("/by_ids", methods = ["DELETE"])
@auth.login_required
def delete_documents():
    doc_ids = request.args.get("ids", "").split(",")
    if not doc_ids:
        raise exceptions.BadRequest()
    (success, changed_objs) = _delete_documents_by_id(doc_ids)
    return jsonify({
        "success": success,
        "changed_objs": changed_objs
    })

def init_app(app):
    app.register_blueprint(bp)
