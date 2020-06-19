# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import json

from flask import abort, Blueprint, jsonify, request
from werkzeug import exceptions

from .. import auth, collections, log
from ..data import service

bp = Blueprint("documents", __name__, url_prefix = "/documents")

def _document_user_can_projection():
    return service.params({"projection": {
        "collection_id": 1
    }})

def user_can_annotate(document):
    return collections.user_can_annotate_by_id(document["collection_id"])

def user_can_view(document):
    return collections.user_can_view_by_id(document["collection_id"])

def user_can_modify_metadata(document):
    return collections.user_can_modify_document_metadata_by_id(document["collection_id"])

def user_can_annotate_by_id(document_id):
    document = service.get_item_by_id("documents", document_id, params=_document_user_can_projection())
    return user_can_annotate(document)

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
        params["projection"] = json.dumps({"metadata": 0})
        params["truncate"] = truncate_length

    if page == "all":
        return jsonify(service.get_all_using_pagination("documents", params))
    
    if page: params["page"] = page
    resp = service.get("documents", params = params)
    if not resp.ok:
        abort(resp.status_code, resp.content)
    data = resp.json()
    if truncate:
        for document in data["_items"]:
            document["text"] = document["text"][0:truncate_length]
    return jsonify(data)

@bp.route("/", strict_slashes = False, methods = ["POST"])
@auth.login_required
def add_document():
    document = request.get_json()
    if not document or "collection_id" not in document or not document["collection_id"]:
        raise exceptions.BadRequest()
    if not collections.user_can_add_documents_or_images_by_id(document["collection_id"]):
        raise exceptions.Unauthorized()
    resp = service.post("documents", json=document)
    if resp.ok:
        log.access_flask_add_document(resp.json())
    return service.convert_response(resp)

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
