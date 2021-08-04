# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import logging
import random
import typing

from flask import abort, Blueprint, jsonify, request, Response
from werkzeug import exceptions

from .. import auth, collections, models
from ..data import service
from ..job_manager.service import ServiceManager, ServiceJob

logger = logging.getLogger(__name__)
service_manager = ServiceManager()

bp = Blueprint("pipelines", __name__, url_prefix = "/pipelines")

# Cache classifiers and overlap so we don't need to keep on making queries
#   we don't need to invalidate cache because we don't invalidate classifiers
_cached_classifiers = {}
_cached_classifier_pipelines = {}

def _get_classifier(classifier_id: str) -> dict:
    if classifier_id not in _cached_classifiers:
        classifier = service.get_item_by_id("/classifiers", classifier_id)
        if classifier is None:
            raise exceptions.NotFound(description="Couldn't find classifier with ID " + classifier_id)
        pipeline_id = classifier["pipeline_id"]
        pipeline = service.get_item_by_id("/pipelines", pipeline_id)
        if pipeline is None:
            raise exceptions.NotFound(description="Couldn't find pipeline with ID " + pipeline_id)
        _cached_classifiers[classifier_id] = classifier
        _cached_classifier_pipelines[classifier_id] = pipeline["name"].lower()
    return _cached_classifiers[classifier_id]

def _clear_classifier(classifier_id: str):
    if classifier_id in _cached_classifiers:
        del _cached_classifiers[classifier_id]
        del _cached_classifier_pipelines[classifier_id]

def _get_classifier_pipeline(classifier_id: str) -> dict:
    # this will populate _cached_classifier_piplines and throw exceptions if needed
    _get_classifier(classifier_id)
    return _cached_classifier_pipelines[classifier_id]

def _check_permissions(classifier: dict):
    collection_id: str = classifier["collection_id"]
    perms: models.CollectionUserPermissions = collections.get_user_permissions_by_id(collection_id)
    if not perms.annotate:
        raise exceptions.Unauthorized()


################################

# Pipeline service methods

def _get_pipeline_status(pipeline: str, classifier_id: str) -> dict:
    job_data = {
        "type": "status",
        "framework": pipeline
    }
    if classifier_id:
        job_data["classifier_id"] = classifier_id
    job: ServiceJob = service_manager.send_service_request_and_get_response(pipeline, job_data, 20)
    return {
        "service_details": service_manager.get_registered_service_details(pipeline),
        "job_id": job.job_id,
        "job_request": job.request_body,
        "job_response": job.request_response
    }

def _get_pipeline_running_jobs(pipeline: str, classifier_id: str) -> typing.List[str]:
    return service_manager.get_running_jobs(pipeline)

def _train_pipeline(pipeline: str, classifier_id: str, model_name: str) -> dict:
    logger.info("Training pipeline='%s' classifier_id='%s' model_name='%s'", pipeline, classifier_id, model_name)
    job_data = {
        "type": "fit",
        "classifier_id": classifier_id,
        "pipeline": pipeline,
        "framework": pipeline,
        "model_name": model_name
    }
    request_body = service_manager.send_service_request(pipeline, job_data)
    return request_body

def _predict_pipeline(pipeline: str, classifier_id: str, document_ids: typing.List[str],
                      texts: typing.List[str], timeout_in_s: int) -> dict:
    job_data = {
        "type": "predict",
        "classifier_id": classifier_id,
        "pipeline": pipeline,
        "framework": pipeline,
        "document_ids": document_ids,
        "texts": texts
    }
    job: ServiceJob = service_manager.send_service_request_and_get_response(
        pipeline, job_data, timeout_in_s)
    return {
        "job_id": job.job_id,
        "job_request": job.request_body,
        "job_response": job.request_response
    }

################################

# Pipeline endpoints

@bp.route("/", strict_slashes = False, methods = ["GET"])
@auth.login_required
def get_pipelines():
    # no permissions check needed; everyone can see pipelines
    return service.convert_response(service.get("pipelines"))

@bp.route("/by_id/<pipeline_id>", methods=["GET"])
def get_pipeline_by_id(pipeline_id: str):
    # no permissions check needed; everyone can see pipelines
    return service.convert_response(service.get("pipelines/" + pipeline_id))

@bp.route("/status/<pipeline_id>", methods=["GET"])
def get_pipeline_status(pipeline_id: str) -> Response:
    # no permissions check needed; everyone can see pipelines
    pipeline = service.get_item_by_id("pipelines", pipeline_id)
    if not pipeline:
        raise exceptions.NotFound()
    pipeline = pipeline["name"].lower()
    return jsonify(_get_pipeline_status(pipeline, None))

################################

# Metrics endpoints

# @bp.route("/metrics", methods=["GET"])
# @auth.login_required
# def get_metrics():
    # resp = service.get("metrics")
    # if not resp.ok:
        # abort(resp.status_code)
    # return service.convert_response(resp)

def _get_classifier_metrics(classifier_id: str):
    _check_permissions(_get_classifier(classifier_id))
    where = {
        "classifier_id": classifier_id
    }
    metrics = service.get_all_items("/metrics", params=service.where_params(where))
    logger.info(metrics)
    if len(metrics) != 1:
        raise exceptions.BadRequest(description="Expected one metric but found {}.".format(len(metrics)))
    all_metrics = service.get_all_versions_of_item_by_id("/metrics", metrics[0]["_id"])
    logger.info(all_metrics)
    return all_metrics

@bp.route("/metrics/by_classifier_id/<classifier_id>", methods=["GET"])
@auth.login_required
def get_classifier_metrics(classifier_id: str):
    return jsonify(_get_classifier_metrics(classifier_id))

################################

# Classifier endpoints

def _get_collection_classifier(collection_id: str) -> dict:
    where = {
        "collection_id": collection_id
    }
    classifiers = service.get_all_items("/classifiers", params=service.where_params(where))
    if len(classifiers) != 1:
        raise exceptions.BadRequest(description="Expected one classifier but found {}.".format(len(classifiers)))
    return classifiers[0]

@bp.route("/classifiers/by_collection_id/<collection_id>", methods=["GET"])
@auth.login_required
def get_collection_classifier(collection_id: str):
    classifier = _get_collection_classifier(collection_id)
    _check_permissions(classifier)
    return jsonify(classifier)

@bp.route("/classifiers/status/<classifier_id>", methods = ["GET"])
@auth.login_required
def get_classifier_status(classifier_id: str):
    classifier = _get_classifier(classifier_id)
    _check_permissions(classifier)
    pipeline = _get_classifier_pipeline(classifier_id)
    return jsonify(_get_pipeline_status(pipeline, classifier_id))

################################

# Classifier endpoints

@bp.route("/running_jobs/<classifier_id>", methods=["GET"])
@auth.login_required
def get_running_jobs(classifier_id: str):
    classifier = _get_classifier(classifier_id)
    _check_permissions(classifier)
    pipeline = _get_classifier_pipeline(classifier_id)
    return jsonify(_get_pipeline_running_jobs(pipeline, classifier_id))

@bp.route("/train/<classifier_id>", methods=["POST"])
def train(classifier_id: str):
    input_json = request.get_json()
    model_name = input_json["model_name"] if "model_name" in input_json else None

    classifier = _get_classifier(classifier_id)
    _check_permissions(classifier)
    pipeline = _get_classifier_pipeline(classifier_id)

    return jsonify({
        "request": _train_pipeline(pipeline, classifier_id, model_name)
    })

@bp.route("/predict/<classifier_id>", methods=["POST"])
@auth.login_required
def predict(classifier_id: str):
    input_json = request.get_json()
    document_ids = input_json.get("document_ids", [])
    texts = input_json.get("texts", [])
    timeout_in_s = input_json.get("timeout_in_s", 36000) # 10 hours
    
    if not isinstance(document_ids, list) or not isinstance(texts, list):
        abort(400, "Error parsing input", custom="document_ids and texts must be lists")
    if len(document_ids) == 0 and len(texts) == 0:
        abort(400, "Error parsing input", custom="At least one of document_ids and texts must be non-empty")
    for document_id in document_ids:
        if not isinstance(document_id, str):
            abort(400, "Error parsing input", custom="Document IDs must be strings")
    for text in texts:
        if not isinstance(text, str):
            abort(400, "Error parsing input", custom="Texts must be strings")
    if not isinstance(timeout_in_s, int):
        abort(400, "Error parsing input", custom="timeout_in_s must be an int")
 
    classifier = _get_classifier(classifier_id)
    _check_permissions(classifier)
    pipeline = _get_classifier_pipeline(classifier_id)
    
    # TODO check that user has permissions for each of the given document IDs

    return _predict_pipeline(pipeline, classifier_id, document_ids, texts, timeout_in_s)

################################

# Next instance endpointsrip

def _get_next_instance(classifier_id: str):
    _check_permissions(_get_classifier(classifier_id))
    items = service.get_all_items("/next_instances", params=service.where_params({"classifier_id": classifier_id}))
    if len(items) == 0:
        raise exceptions.NotFound(description="No next instances")
    return items[0]

def _check_instance_overlap(classifier: dict, instance: dict, user_id: str):
    if user_id not in instance["overlap_document_ids"]:
        logger.info("new user: adding to overlap document ids")
        instance["overlap_document_ids"][user_id] = collections.get_overlap_ids(classifier["collection_id"])
        to_patch = {
            "_id": instance["_id"],
            "overlap_document_ids": instance["overlap_document_ids"]
        }
        headers = {"If-Match": instance["_etag"]}
        r = service.patch(["next_instances", instance["_id"]], json = to_patch, headers = headers)
        if not r.ok:
            abort(r.status_code, r.content)

@bp.route("/next_document/by_classifier_id/<classifier_id>", methods = ["GET"])
@auth.login_required
def get_next_by_classifier(classifier_id: str):
    instance = _get_next_instance(classifier_id)
    classifier = _get_classifier(classifier_id)
    _check_permissions(classifier)
    
    user_id = auth.get_logged_in_user()["id"]
    _check_instance_overlap(classifier, instance, user_id)

    if random.random() <= classifier["overlap"] and len(instance["overlap_document_ids"][user_id]) > 0:
        return jsonify(instance["overlap_document_ids"][user_id].pop())
    elif len(instance["document_ids"]) > 0:
        return jsonify(instance["document_ids"].pop())
    elif len(instance["overlap_document_ids"][user_id]) > 0:
        return jsonify(instance["overlap_document_ids"][user_id].pop())
    else:
        return jsonify(None)

@bp.route("/next_document/by_classifier_id/<classifier_id>/<document_id>", methods = ["POST"])
@auth.login_required
def advance_to_next_document_by_classifier(classifier_id: str, document_id: str):
    user_id = auth.get_logged_in_user()["id"]
    
    # reset classifier_dict for classifier, cached classifiers are getting out of sync
    _clear_classifier(classifier_id)
        
    classifier = _get_classifier(classifier_id)
    _check_permissions(classifier)

    pipeline = _get_classifier_pipeline(classifier_id)
    instance = _get_next_instance(classifier_id)
    
    _check_instance_overlap(classifier, instance, user_id)

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

        classifier["annotated_document_count"] += 1
        headers = {"If-Match": classifier["_etag"]}
        service.remove_nonupdatable_fields(classifier)
        r = service.patch(["classifiers", classifier_id], json=classifier, headers=headers)
        if not r.ok:
            abort(r.status_code, r.content)
        _clear_classifier(classifier_id)
        classifier = _get_classifier(classifier_id)

        if classifier["annotated_document_count"] % classifier["train_every"] == 0:
            ## Check to see if we should update classifier
            ## Add to work queue to update classifier - queue is pipeline_id
            ## ADD TO PUBSUB {classifier_id} to reload
            request_body = _train_pipeline(pipeline, classifier_id, "auto-trained")
            trained = True

    return jsonify({
        "success": True,
        "trained": trained,
        "body": request_body
    })

################################

def init_app(app):
    service_manager.start_listeners()
    app.register_blueprint(bp)
