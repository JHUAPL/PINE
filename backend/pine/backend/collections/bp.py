# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import csv
import io
import json
import logging
import os
import random
import traceback
import unicodedata

from flask import abort, Blueprint, current_app, jsonify, request, safe_join, send_file, send_from_directory
from werkzeug import exceptions

from .. import auth, log
from ..data import service

bp = Blueprint("collections", __name__, url_prefix = "/collections")
LOGGER = logging.getLogger(__name__)

DOCUMENTS_PER_TRANSACTION = 500

# Cache this info for uploading large numbers of images sequentially
LAST_COLLECTION_FOR_IMAGE = None
def is_cached_last_collection(collection_id):
    global LAST_COLLECTION_FOR_IMAGE
    return LAST_COLLECTION_FOR_IMAGE and LAST_COLLECTION_FOR_IMAGE[0] == collection_id and LAST_COLLECTION_FOR_IMAGE[1] == auth.get_logged_in_user()["id"]
def update_cached_last_collection(collection_id):
    global LAST_COLLECTION_FOR_IMAGE
    LAST_COLLECTION_FOR_IMAGE = [collection_id, auth.get_logged_in_user()["id"]]

def _collection_user_can_projection():
    return service.params({
        "projection": {
            "creator_id": 1,
            "annotators": 1,
            "viewers": 1
        }
    })

def _collection_user_can(collection, annotate):
    user_id = auth.get_logged_in_user()["id"]
    if annotate and not auth.is_flat():
        return collection["creator_id"] == user_id or user_id in collection["annotators"]
    else:
        return collection["creator_id"] == user_id or user_id in collection["viewers"] or user_id in collection["annotators"]

def user_can_annotate(collection):
    return _collection_user_can(collection, annotate = True)

def user_can_view(collection):
    return _collection_user_can(collection, annotate = False)

def user_can_add_documents_or_images(collection):
    # for now, this is the same thing as just being able to view
    return user_can_view(collection)

def user_can_modify_document_metadata(collection):
    # for now, this is the same thing as just being able to view
    return user_can_view(collection)

def user_can_annotate_by_id(collection_id):
    collection = service.get_item_by_id("/collections", collection_id, _collection_user_can_projection())
    return _collection_user_can(collection, annotate = True)

def user_can_annotate_by_ids(collection_ids):
    collections = service.get_items("collections", params=service.params({
        "where": {
            "_id": {"$in": collection_ids}
        }, "projection": {
            "creator_id": 1,
            "annotators": 1,
            "viewers": 1
        }
    }))
    for collection in collections:
        if not user_can_annotate(collection):
            return False
    return True

def user_can_view_by_id(collection_id):
    collection = service.get_item_by_id("/collections", collection_id, _collection_user_can_projection())
    return _collection_user_can(collection, annotate = False)

def user_can_add_documents_or_images_by_id(collection_id):
    collection = service.get_item_by_id("/collections", collection_id, _collection_user_can_projection())
    return user_can_add_documents_or_images(collection)

def user_can_modify_document_metadata_by_id(collection_id):
    collection = service.get_item_by_id("/collections", collection_id, _collection_user_can_projection())
    return user_can_modify_document_metadata(collection)


def get_user_collections(archived, page):
    """
    Return collections for the logged in user using pagination. Returns all collections if parameter "page" is "all",
    or the collections associated with the given page. Can return archived or un-archived collections based upon the
    "archived" flag.
    :param archived: Bool
    :param page: str
    :return: Response
    """
    user_id = auth.get_logged_in_user()["id"]
    where = {
        "archived": archived,
        "$or": [
            {"creator_id": user_id},
            {"viewers": user_id},
            {"annotators": user_id}
        ]
    }
    params = service.where_params(where)
    if page == "all":
        return jsonify(service.get_all_using_pagination("collections", params))
    if page: params["page"] = page
    resp = service.get("collections", params = params)
    return service.convert_response(resp)

@bp.route("/unarchived", defaults = {"page": "all"}, methods = ["GET"])
@bp.route("/unarchived/<page>", methods = ["GET"])
@auth.login_required
def get_unarchived_user_collections(page):
    """
    Return unarchived user collections for the corresponding page value. Default value returns collections for all
    pages.
    :param page: str
    :return: Response
    """
    return get_user_collections(False, page)

@bp.route("/archived", defaults = {"page": "all"}, methods = ["GET"])
@bp.route("/archived/<page>", methods = ["GET"])
@auth.login_required
def get_archived_user_collections(page):
    """
    Return archived user collections for the corresponding page value. Default value returns collections for all
    pages.
    :param page: str
    :return: Response
    """
    return get_user_collections(True, page)

def archive_or_unarchive_collection(collection_id, archive):
    """
    Set the "archived" boolean flag for the collection matching the provided collection_id.
    :param collection_id: str
    :param archive: Bool
    :return: Response
    """
    user_id = auth.get_logged_in_user()["id"]
    resp = service.get("collections/" + collection_id)
    if not resp.ok:
        abort(resp.status_code)
    collection = resp.json()
    if not auth.is_flat() and collection["creator_id"] != user_id:
        raise exceptions.Unauthorized("Only the creator can archive a collection.")
    collection["archived"] = archive
    headers = {"If-Match": collection["_etag"]}
    service.remove_nonupdatable_fields(collection)
    resp = service.put(["collections", collection_id], json = collection, headers = headers)
    if not resp.ok:
        abort(resp.status_code)
    return get_collection(collection_id)

@bp.route("/archive/<collection_id>", methods = ["PUT"])
@auth.login_required
def archive_collection(collection_id):
    """
    Archive the collection matching the provided collection id
    :param collection_id: str
    :return: Response
    """
    return archive_or_unarchive_collection(collection_id, True)

@bp.route("/unarchive/<collection_id>", methods = ["PUT"])
@auth.login_required
def unarchive_collection(collection_id):
    """
    Unarchive the collection matching the provided collection id
    :param collection_id: str
    :return: Response
    """
    return archive_or_unarchive_collection(collection_id, False)

@bp.route("/by_id/<collection_id>", methods = ["GET"])
@auth.login_required
def get_collection(collection_id):
    """
    Return the collection object for the collection matching the provided collection id. This object has the fields:
    'creator_id', 'annotators', 'viewers', 'labels', 'metadata', 'archived', and 'configuration'.
    :param collection_id: str
    :return: Response
    """
    resp = service.get(["collections", collection_id])
    if not resp.ok:
        abort(resp.status_code)
    collection = resp.json()
    if user_can_view(collection):
        return service.convert_response(resp)
    else:
        raise exceptions.Unauthorized()

@bp.route("/by_id/<collection_id>/download", methods = ["GET"])
@auth.login_required
def download_collection(collection_id):
    resp = service.get(["collections", collection_id])
    if not resp.ok:
        abort(resp.status_code)
    collection = resp.json()
    if not user_can_view(collection):
        return exceptions.Unauthorized()
    
    def flag(name): return name not in request.args or json.loads(request.args[name])
    include_collection_metadata = flag("include_collection_metadata")
    include_document_metadata = flag("include_document_metadata")
    include_document_text = flag("include_document_text")
    include_annotations = flag("include_annotations")
    include_annotation_latest_version_only = flag("include_annotation_latest_version_only")
    as_file = flag("as_file")

    if include_collection_metadata:
        col = dict(collection)
        service.remove_eve_fields(col)
        data = col
    else:
        data = {
            "_id": collection["_id"]
        }

    params = service.where_params({
        "collection_id": collection_id
    })
    if not include_document_metadata and not include_document_text:
        params["projection"] = json.dumps({
            "_id": 1
        })
    elif not include_document_metadata:
        params["projection"] = json.dumps({
            "_id": 1,
            "text": 1
        })
    elif not include_document_text:
        params["projection"] = json.dumps({
            "text": 0,
            "collection_id": 0
        })
    else:
        params["projection"] = json.dumps({
            "collection_id": 0
        })

    data["documents"] = service.get_all_using_pagination("documents", params)["_items"]

    annotations_by_document = {}
    if include_annotations:
        params = service.params({
            "where": {
                "collection_id": collection_id
            },
            "projection": {
                "collection_id": 0
            }
        })
        annotations = service.get_all_using_pagination("annotations", params)["_items"]
        for annotation in annotations:
            doc_id = annotation["document_id"]
            del annotation["document_id"]
            if doc_id not in annotations_by_document:
                annotations_by_document[doc_id] = []
            annotations_by_document[doc_id].append(annotation)

    for document in data["documents"]:
        service.remove_eve_fields(document)
        if include_annotations and document["_id"] in annotations_by_document:
            annotations = annotations_by_document[document["_id"]]
            if include_annotation_latest_version_only:
                document["annotations"] = annotations
            else:
                params = service.params({
                    "projection": {
                        "collection_id": 0,
                        "document_id": 0
                    }
                })
                document["annotations"] = []
                for annotation in annotations:
                    all_versions = service.get_all_versions_of_item_by_id("annotations", annotation["_id"],
                                                                          params=params)
                    document["annotations"] += all_versions["_items"]
            for annotation in document["annotations"]:
                service.remove_eve_fields(annotation,
                                          remove_versions = include_annotation_latest_version_only)

    if as_file:
        data_bytes = io.BytesIO()
        data_bytes.write(json.dumps(data).encode())
        data_bytes.write(b"\n")
        data_bytes.seek(0)

        return send_file(
            data_bytes,
            as_attachment=True,
            attachment_filename="collection_{}.json".format(collection_id),
            mimetype="application/json"
        )
    else:
        return jsonify(data)

def get_doc_and_overlap_ids(collection_id):
    """
    Return lists of ids for overlapping and non-overlapping documents for the collection matching the provided
    collection id.
    :param collection_id: str
    :return: tuple
    """
    params = service.params({
        "where": {"collection_id": collection_id, "overlap": 0},
        "projection": {"_id": 1}
    })
    doc_ids = [doc["_id"] for doc in service.get_all_using_pagination("documents", params)['_items']]
    # doc_ids = get_all_ids("documents?where={\"collection_id\":\"%s\",\"overlap\":0}"%(collection_id))
    random.shuffle(doc_ids)
    overlap_ids = get_overlap_ids(collection_id)
    return (doc_ids, overlap_ids)


@bp.route("/add_annotator/<collection_id>", methods=["POST"])
@auth.login_required
def add_annotator_to_collection(collection_id):
    user_id = json.loads(request.form["user_id"])
    resp = service.get(["collections", collection_id])
    if not resp.ok:
        abort(resp.status_code)
    collection = resp.json()
    auth_id = auth.get_logged_in_user()["id"]
    if not (collection["creator_id"] == auth_id):
        raise exceptions.Unauthorized()
    if user_id not in collection["annotators"]:
        LOGGER.info("new annotator: adding to collection")
        collection["annotators"].append(user_id)
        if user_id not in collection["viewers"]:
            collection["viewers"].append(user_id)
            to_patch = {
                "annotators": collection["annotators"],
                "viewers": collection["viewers"]
            }
        else:
            to_patch = {
                "annotators": collection["annotators"]
            }
        headers = {'Content-Type': 'application/json', 'If-Match': collection["_etag"]}
        resp = service.patch(["collections", collection["_id"]], json=to_patch, headers=headers)
        if not resp.ok:
            abort(resp.status_code, resp.content)
        return service.convert_response(resp)
    else:
        abort(409, "Annotator already exists in collection")


@bp.route("/add_viewer/<collection_id>", methods=["POST"])
@auth.login_required
def add_viewer_to_collection(collection_id):
    user_id = json.loads(request.form["user_id"])
    resp = service.get(["collections", collection_id])
    if not resp.ok:
        abort(resp.status_code)
    collection = resp.json()
    auth_id = auth.get_logged_in_user()["id"]
    if not (collection["creator_id"] == auth_id):
        raise exceptions.Unauthorized()
    if user_id not in collection["viewers"]:
        LOGGER.info("new viewer: adding to collection")
        collection["viewers"].append(user_id)
        to_patch = {
            "viewers": collection["viewers"]
        }
        headers = {'Content-Type': 'application/json', 'If-Match': collection["_etag"]}
        resp = service.patch(["collections", collection["_id"]], json=to_patch, headers=headers)
        if not resp.ok:
            abort(resp.status_code, resp.content)
        return service.convert_response(resp)
    else:
        abort(409, "Annotator already exists in collection")


@bp.route("/add_label/<collection_id>", methods=["POST"])
@auth.login_required
def add_label_to_collection(collection_id):
    new_label = json.loads(request.form["new_label"])
    resp = service.get(["collections", collection_id])
    if not resp.ok:
        abort(resp.status_code)
    collection = resp.json()
    auth_id = auth.get_logged_in_user()["id"]
    if not (collection["creator_id"] == auth_id):
        raise exceptions.Unauthorized()
    if new_label not in collection["labels"]:
        LOGGER.info("new label: adding to collection")
        collection["labels"].append(new_label)
        to_patch = {
            "labels": collection["labels"]
        }
        headers = {'Content-Type': 'application/json', 'If-Match': collection["_etag"]}
        resp = service.patch(["collections", collection["_id"]], json=to_patch, headers=headers)
        if not resp.ok:
            abort(resp.status_code, resp.content)
        return service.convert_response(resp)
    else:
        abort(409, "Annotator already exists in collection")


def get_overlap_ids(collection_id):
    """
    Return the list of ids for overlapping documents for the collection matching the provided collection id.
    :param collection_id: str
    :return: tuple
    """
    where = {"collection_id": collection_id, "overlap": 1}
    params = service.where_params(where)
    return [doc["_id"] for doc in service.get_all_using_pagination("documents", params)['_items']]


def _upload_documents(collection, docs):
    doc_resp = service.post("/documents", json=docs)
    # TODO if it failed, roll back the created collection and classifier
    if not doc_resp.ok:
        abort(doc_resp.status_code, doc_resp.content)
    r = doc_resp.json()
    # TODO if it failed, roll back the created collection and classifier
    if r["_status"] != "OK":
        abort(400, "Unable to create documents")
    for obj in r["_items"]:
        if obj["_status"] != "OK":
            abort(400, "Unable to create documents")
    doc_ids = [obj["_id"] for obj in r["_items"]]
    LOGGER.info("Added {} docs to collection {}".format(len(doc_ids), collection["_id"]))
    return doc_ids

# Require a multipart form post:
# CSV is in the form file "file"
# Optional images are in the form file fields "imageFileN" where N is an (ignored) index
# If CSV is provided, the fields "csvTextCol" and "csvHasHeader" must also be provided in the form
# Collection jSON string is in the form field "collection"
# Pipeline ID is in the form field "pipelineId"
# Overlap is in the form field "overlap"
# Train every is in the form field "train_every"
# Any classifier parameters are in the form field "classifierParameters"
@bp.route("/", strict_slashes = False, methods = ["POST"])
@auth.login_required
def create_collection():
    # If you change the requirements here, also update the client module pine.client.models
    """
    Create a new collection based upon the entries provided in the POST request's associated form fields.
    These fields include:
    collection - collection name
    overlap - ratio of overlapping documents. (0-1) with 0 being no overlap and 1 being every document has overlap, ex:
        .90 - 90% of documents overlap
    train_every - automatically train a new classifier after this many documents have been annotated
    pipelineId - the id value of the classifier pipeline associated with this collection (spacy, opennlp, corenlp)
    classifierParameters - optional parameters that adjust the configuration of the chosen classifier pipeline.
    archived - whether or not this collection should be archived.
    A collection can be created with documents listed in a csv file. Each new line in the csv represents a new document.
    The data of this csv can be passed to this method through the POST request's FILES field "file".
    used when creating a collection based on an uploaded csv file:
        csvTextCol - column of csv containing the text of the documents (default: 0)
        csvHasHeader - boolean for whether or not the csv file has a header row (default: False)
    A collection can also be created with a number of images through FILES fields "imageFileN" where N is an (ignored) index
    :return: information about the created collection
    """
    user_id = auth.get_logged_in_user()["id"]
    try:
        #posted_file = StringIO(str(request.files["document"].read(), "utf-8"))
        #posted_data = json.loads(str(request.files["data"].read(), "utf-8"))
        if "file" in request.files:
            posted_file = io.StringIO(str(request.files["file"].read(), "utf-8-sig"))
            csv_text_col = json.loads(request.form["csvTextCol"])
            csv_has_header = json.loads(request.form["csvHasHeader"])
        else:
            posted_file = None
            csv_text_col = None
            csv_has_header = None
        collection = json.loads(request.form["collection"])
        overlap = json.loads(request.form["overlap"])
        train_every = json.loads(request.form["train_every"])
        pipeline_id = json.loads(request.form["pipelineId"])
        if "classifierParameters" in request.form:
            classifier_parameters = json.loads(request.form["classifierParameters"])
        else:
            classifier_parameters = None
        image_files = []
        for key in request.files:
            if key and key.startswith("imageFile"):
                image_files.append(request.files[key])
    except Exception as e:
        traceback.print_exc()
        abort(400, "Error parsing input:" + str(e))

    if collection["creator_id"] != user_id:
        abort(exceptions.Unauthorized, "Can't create collections for other users.")
    if "archived" not in collection:
        collection["archived"] = False
    if "configuration" not in collection:
        collection["configuration"] = {}

    # create collection
    create_resp = service.post("/collections", json = collection)
    if not create_resp.ok:
        abort(create_resp.status_code, create_resp.content)
    r = create_resp.json()
    if r["_status"] != "OK":
        abort(400, "Unable to create collection")

    collection_id = r["_id"]
    collection["_id"] = collection_id
    log.access_flask_add_collection(collection)
    LOGGER.info("Created collection {}".format(collection_id))

    #create classifier
    #   require collection_id, overlap, pipeline_id and labels
    classifier_obj = {"collection_id": collection_id,
                      "overlap": overlap,
                      "pipeline_id": pipeline_id,
                      #"parameters": pipeline_params,
                      "labels": collection["labels"],
                      "train_every": train_every}
    # filename?
    if classifier_parameters:
        classifier_obj["parameters"] = classifier_parameters
        
    classifier_resp = service.post("/classifiers", json = classifier_obj)
    # TODO: if it failed, roll back the created collection
    if not classifier_resp.ok:
        abort(classifier_resp.status_code, classifier_resp.content)
    r = classifier_resp.json()
    if r["_status"] != "OK":
        abort(400, "Unable to create classifier")
    classifier_id = r["_id"]
    LOGGER.info("Created classifier {}".format(classifier_id))

    # create metrics for classifier
    # require collection_id, classifier_id, document_ids and annotations ids
    metrics_obj = {"collection_id": collection_id,
                      "classifier_id": classifier_id,
                      "documents": list(),
                      "annotations": list(),
                      "folds": list(),
                      "metrics": list()
                      }
    metrics_resp = service.post("/metrics", json = metrics_obj)
    # TODO: if it failed, roll back the created collection
    if not metrics_resp.ok:
        abort(metrics_resp.status_code, metrics_resp.content)
    r = metrics_resp.json()
    if r["_status"] != "OK":
        abort(400, "Unable to create metrics")
    metrics_id = r["_id"]
    LOGGER.info("Created metrics {}".format(metrics_id))

    #create documents if CSV file was sent in
    doc_ids = []
    if posted_file != None:
        docs = []
        csvreader = csv.reader(posted_file)
        first = True
        headers = None
        initial_has_annotated_dict = {}
        for ann_id in collection["annotators"]:
            initial_has_annotated_dict[ann_id] = False
        for row in csvreader:
            if len(row) == 0: continue # empty row
            if first and csv_has_header:
                headers = row
                first = False
                continue
            metadata = {}
            if csv_has_header:
                if len(row)!=len(headers):
                    continue
                for i in range(len(row)):
                    if i != csv_text_col:
                        metadata[headers[i]] = row[i]
            doc = {
                "creator_id": user_id,
                "collection_id": collection_id,
                "text": row[csv_text_col],
                "metadata": metadata,
                "has_annotated" : initial_has_annotated_dict
            }
            if random.random() < overlap:
                doc["overlap"] = 1
            else:
                doc["overlap"] = 0
            docs.append(doc)
            if len(docs) >= DOCUMENTS_PER_TRANSACTION:
                doc_ids += _upload_documents(collection, docs)
                docs = []
        if len(docs) > 0:
            doc_ids += _upload_documents(collection, docs)
            docs = []

    # create next ids
    (doc_ids, overlap_ids) = get_doc_and_overlap_ids(collection_id)
    overlap_obj = {
        "classifier_id": classifier_id,
        "document_ids": doc_ids,
        "overlap_document_ids": { ann_id: overlap_ids for ann_id in collection["annotators"] }
    }
    #for ann_id in collection["annotators"]:
    #    overlap_obj["overlap_document_ids"][ann_id] = overlap_ids
    # TODO if it failed, roll back the created collection and classifier and documents
    instances_response = service.post("/next_instances", json=overlap_obj)
    if not instances_response.ok:
        abort(instances_response.status_code, instances_response.content)
    #post_items("next_instances", overlap_obj)
    doc_ids.extend(overlap_ids)

    # upload any image files
    for image_file in image_files:
        _upload_collection_image_file(collection_id, image_file.filename, image_file)

    return service.convert_response(create_resp)

def _check_collection_and_get_image_dir(collection_id, path):
    # make sure user can view collection
    if not is_cached_last_collection(collection_id):
        if not user_can_view_by_id(collection_id):
            raise exceptions.Unauthorized()

    image_dir = current_app.config["DOCUMENT_IMAGE_DIR"]
    if image_dir == None or len(image_dir) == 0:
        raise exceptions.InternalServerError()

    # "static" is a special path that grabs images not associated with a particular collection
    # this is mostly for testing
    if not path.startswith("static/"):
        image_dir = os.path.join(image_dir, "by_collection", collection_id)

    return os.path.realpath(image_dir)

@bp.route("/static_images/<collection_id>", methods=["GET"])
@auth.login_required
def get_static_collection_images(collection_id):
    static_image_dir = os.path.join(_check_collection_and_get_image_dir(collection_id, "static/"), "static")
    urls = []
    for _, _, filenames in os.walk(static_image_dir):
        urls += ["/static/{}".format(f) for f in filenames]
    return jsonify(urls)

@bp.route("/images/<collection_id>", methods=["GET"])
@auth.login_required
def get_collection_images(collection_id):
    collection_image_dir = _check_collection_and_get_image_dir(collection_id, "")
    urls = []
    for _, _, filenames in os.walk(collection_image_dir):
        urls += ["/{}".format(f) for f in filenames]
    return jsonify(urls)

@bp.route("/image/<collection_id>/<path:path>", methods=["GET"])
@auth.login_required
def get_collection_image(collection_id, path):
    image_dir = _check_collection_and_get_image_dir(collection_id, path)
    return send_from_directory(image_dir, path)

@bp.route("/image_exists/<collection_id>/<path:path>", methods=["GET"])
@auth.login_required
def get_collection_image_exists(collection_id, path):
    image_dir = _check_collection_and_get_image_dir(collection_id, path)
    image_file = safe_join(image_dir, path)
    return jsonify(os.path.isfile(image_file))

def _path_split(path): # I can't believe there's no os.path function to do this
    dirs = []
    while True:
        (path, d) = os.path.split(path)
        if d != "":
            dirs.append(d)
        else:
            if path != "":
                dirs.append(path)
            break
    dirs.reverse()
    return dirs

def _safe_path(path):
    # inspired by safe_filename() from werkzeug but allowing /'s
    path = unicodedata.normalize("NFKD", path).encode("ascii", "ignore").decode("ascii")
    if path.startswith("/"):
        path = path[1:]
    if path.endswith("/"):
        path = path[0:-1]
    return "/".join([p for p in _path_split(path) if p not in [".", "/", ".."]])

@bp.route("/can_add_documents_or_images/<collection_id>", methods=["GET"])
@auth.login_required
def get_user_can_add_documents_or_images(collection_id):
    return jsonify(user_can_add_documents_or_images_by_id(collection_id))

def _upload_collection_image_file(collection_id, path, image_file):
    # get filename on disk to save to
    path = _safe_path(path)
    image_dir = _check_collection_and_get_image_dir(collection_id, path)
    image_filename = os.path.realpath(os.path.join(image_dir, path))
    if not image_filename.startswith(image_dir): # this shouldn't happen but just to be sure
        raise exceptions.BadRequest("Invalid path.")
    if not os.path.isdir(os.path.dirname(image_filename)):
        os.makedirs(os.path.dirname(image_filename))

    # save image
    image_file.save(image_filename)
    return "/" + path

@bp.route("/image/<collection_id>/<path:path>", methods=["POST", "PUT"])
@auth.login_required
def post_collection_image(collection_id, path):
    if not is_cached_last_collection(collection_id):
        if not user_can_add_documents_or_images_by_id(collection_id):
            raise exceptions.Unauthorized()
    if "file" not in request.files:
        raise exceptions.BadRequest("Missing file form part.")

    update_cached_last_collection(collection_id)

    return jsonify(_upload_collection_image_file(collection_id, path, request.files["file"]))

def init_app(app):
    app.register_blueprint(bp)
