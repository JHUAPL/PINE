# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import json
import logging
import pydash
import random
import uuid

from flask import abort, Blueprint, jsonify, request
from werkzeug import exceptions

from .. import auth
from ..data import service
from ..collections import bp as collectionsbp
from ..job_manager.service import ServiceManager

logger = logging.getLogger(__name__)
service_manager = ServiceManager()

bp = Blueprint("pipelines", __name__, url_prefix = "/pipelines")

# Cache classifiers and overlap so we don't need to keep on making queries
#   we don't need to invalidate cache because we don't invalidate classifiers
classifier_dict = {}
classifier_pipelines = {}


@bp.route("/", strict_slashes = False, methods = ["GET"])
@auth.login_required
def get_pipelines():
    resp = service.get("pipelines")
    if not resp.ok:
        abort(resp.status_code)
    return service.convert_response(resp)

@bp.route("/by_id/<pipeline_id>", methods = ["GET"])
def get_pipeline_by_id(pipeline_id):
    resp = service.get("pipelines/" + pipeline_id)
    return service.convert_response(resp)

def _get_collection_classifier(collection_id):
    where = {
        "collection_id": collection_id
    }
    classifiers = service.get_items("/classifiers", params=service.where_params(where))
    if len(classifiers) != 1:
        raise exceptions.BadRequest(description="Expected one classifier but found {}.".format(len(classifiers)))
    return classifiers[0]


@bp.route("/classifiers/by_collection_id/<collection_id>", methods=["GET"])
@auth.login_required
def get_collection_classifier(collection_id):
    return jsonify(_get_collection_classifier(collection_id))


def _get_classifier_metrics(classifier_id):
    where = {
        "classifier_id": classifier_id
    }
    metrics = service.get_items("/metrics", params=service.where_params(where))
    logger.info(metrics)
    if len(metrics) != 1:
        raise exceptions.BadRequest(description="Expected one metric but found {}.".format(len(metrics)))
    all_metrics = service.get_all_versions_of_item_by_id("/metrics", metrics[0]["_id"])
    logger.info(all_metrics)
    return all_metrics

def _get_collection_classifier(collection_id):
    where = {
        "collection_id": collection_id
    }
    classifiers = service.get_items("/classifiers", params=service.where_params(where))
    if len(classifiers) != 1:
        raise exceptions.BadRequest(description="Expected one classifier but found {}.".format(len(classifiers)))
    return classifiers[0]


@bp.route("/metrics", methods=["GET"])
@auth.login_required
def get_metrics():
    resp = service.get("metrics")
    if not resp.ok:
        abort(resp.status_code)
    return service.convert_response(resp)


@bp.route("/metrics/by_classifier_id/<classifier_id>", methods=["GET"])
# @auth.login_required
def get_classifier_metrics(classifier_id):
    return jsonify(_get_classifier_metrics(classifier_id))


def _get_classifier(classifier_id):
    classifier = service.get_item_by_id("/classifiers", classifier_id)
    if classifier is None:
        return False
    else:
        pipeline = service.get_item_by_id("/pipelines", classifier["pipeline_id"])
        if pipeline is None:
            return False
        else:
            classifier_dict[classifier_id] = classifier
            classifier_pipelines[classifier_id] = pipeline["name"].lower()
            return True


def _get_next_instance(classifier_id):
    if classifier_id not in classifier_dict:
        if not _get_classifier(classifier_id):
            raise exceptions.NotFound(description = "Classifier not found: could not load classifier.")
    items = service.get_items("/next_instances", service.where_params({"classifier_id": classifier_id}))
#     r = requests.get(ENTRY_POINT + '/next_instances?where={"classifier_id":"' + classifier_id + '"}',
#                      headers=EVE_HEADERS)
#     items = get_items_from_response(r)["_items"]
    if len(items) == 0:
        raise exceptions.NotFound("No next instances")
    return items[0]


@bp.route("/next_document/by_classifier_id/<classifier_id>", methods = ["GET"])
@auth.login_required
def get_next_by_classifier(classifier_id):
    instance = _get_next_instance(classifier_id)
    user_id = auth.get_logged_in_user()["id"]

    if user_id not in instance["overlap_document_ids"]:
        print("new user: adding to overlap document ids")
        instance["overlap_document_ids"][user_id] = collectionsbp.get_overlap_ids(classifier_dict[classifier_id]["collection_id"])
        to_patch = {
            "_id": instance["_id"],
            "overlap_document_ids": instance["overlap_document_ids"]
        }
        headers = {"If-Match": instance["_etag"]}
        r = service.patch(["next_instances", instance["_id"]], json = to_patch, headers = headers)
        if not r.ok:
            abort(r.status_code, r.content)

    if random.random() <= classifier_dict[classifier_id]["overlap"] and len(instance["overlap_document_ids"][user_id]) > 0:
        return jsonify(instance["overlap_document_ids"][user_id].pop())
    elif len(instance["document_ids"]) > 0:
        return jsonify(instance["document_ids"].pop())
    else:
        return jsonify(None)


@bp.route("/next_document/by_classifier_id/<classifier_id>/<document_id>", methods = ["POST"])
@auth.login_required
def advance_to_next_document_by_classifier(classifier_id, document_id):
    user_id = auth.get_logged_in_user()["id"]
    
    # get stored next data
    if classifier_id not in classifier_dict:
        if not _get_classifier(classifier_id):
            raise exceptions.NotFound(description="Classifier not found: could not load classifier.")
    else:
        # reset classifier_dict for classifier, cached classifiers are getting out of sync
        del classifier_dict[classifier_id]
        if not _get_classifier(classifier_id):
            raise exceptions.NotFound(description="Classifier not found: could not load classifier.")
        logger.debug(classifier_dict[classifier_id])
    pipeline = pydash.get(classifier_pipelines, classifier_id, None)
    if pipeline is None:
        return jsonify("Error, pipeline not found"), 500
    instance = _get_next_instance(classifier_id)

    data = None
    trained = False
    request_body = None

    if document_id in instance["overlap_document_ids"][user_id]:
        instance["overlap_document_ids"][user_id].remove(document_id)
        data = {"overlap_document_ids": instance["overlap_document_ids"]}
    elif document_id in instance["document_ids"]:
        instance["document_ids"].remove(document_id)
        data = {"document_ids": instance["document_ids"]}
    else:
        logger.info("Document {} not found in instance, document already annotated".format(document_id))

    if data is not None:
        headers = {"If-Match": instance["_etag"]}
        r = service.patch(["next_instances", instance["_id"]], json = data, headers = headers)
        #r = requests.patch(ENTRY_POINT + "/next_instances/" + items[0]["_id"], json.dumps(data), headers=headers)
        if not r.ok:
            abort(r.status_code, r.content)

        classifier_dict[classifier_id]["annotated_document_count"] += 1
        headers = {"If-Match": classifier_dict[classifier_id]["_etag"]}
        service.remove_nonupdatable_fields(classifier_dict[classifier_id])
        r = service.patch(["classifiers", classifier_id], json=classifier_dict[classifier_id], headers=headers)
        if not r.ok:
            abort(r.status_code, r.content)
        del classifier_dict[classifier_id]
        if not _get_classifier(classifier_id):
            raise exceptions.NotFound(description="Classifier not found: could not load classifier.")

        if classifier_dict[classifier_id]["annotated_document_count"] % classifier_dict[classifier_id]["train_every"] == 0:
            ## Check to see if we should update classifier
            ## Add to work queue to update classifier - queue is pipeline_id
            ## ADD TO PUBSUB {classifier_id} to reload
            logger.info("training")
            job_data = {'classifier_id': classifier_id, 'pipeline': pipeline, 'type': 'fit', 'framework': pipeline,
                        'model_name': 'auto-trained'}
            request_body = service_manager.send_service_request(pipeline, job_data)
            trained = True

    return jsonify({"success": True, "trained": trained, "body": request_body})


@bp.route("/predict", methods=["POST"])
@auth.login_required
def predict():
    try:
        input_json = request.get_json()
        classifier_id = input_json["classifier_id"]
        documents = input_json["documents"]
        docids = input_json["document_ids"]
    except Exception as e:
        abort(400, "Error parsing input", custom="Input JSON could not be read:" + str(e))
 
    if classifier_id not in classifier_dict:
        if not _get_classifier(classifier_id):
            raise exceptions.NotFound(description = "Classifier not found: could not load classifier.")
    pipeline_id = classifier_dict[classifier_id]["pipeline_id"]
    ##enqueue documents and ids - CHECK THIS MAY NOT WORK!
    key = "{}:result:{}".format(pipeline_id, uuid.uuid4())
    service_manager.send_service_request(pipeline_id, json.dumps({"type": "predict", "documents": documents,
                                                                 "document_ids": docids, "classifier_id": classifier_id,
                                                                 "response_key": key}))
    # alternatively use session key but might need more work to integrate with authentication, nginx
    # session["predict_result_key"] = key
    return jsonify({"response_key": key})


@bp.route("/train", methods=["POST"])
def test_redis():
    # try:
    input_json = request.get_json()
    classifier_id = pydash.get(input_json, "classifier_id", None)
    # get classifier and pipeline
    if classifier_id not in classifier_dict:
        if not _get_classifier(classifier_id):
            return jsonify("Error, classifier not found"), 500
    pipeline = pydash.get(classifier_pipelines, classifier_id, None)
    if pipeline is None:
        return jsonify("Error, pipeline not found"), 500
    model_name = pydash.get(input_json, "model_name", None)
    logger.info(service_manager.get_registered_channels())
    job_data = {'classifier_id': classifier_id, 'pipeline': pipeline, 'type': 'fit', 'framework': pipeline,
                'model_name': model_name}
    request_body = service_manager.send_service_request(pipeline, job_data)
    return jsonify({"request": request_body})


def init_app(app):
    service_manager.start_listeners()
    app.register_blueprint(bp)
