# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import logging

from flask import abort, Blueprint, jsonify

from .. import auth
from ..data import service
from ..pineiaa.bratiaa import iaa_service

logger = logging.getLogger(__name__)

bp = Blueprint("iaa_reports", __name__, url_prefix = "/iaa_reports")

def get_current_report(collection_id):
    where = {
        "collection_id": collection_id,
    }
    reports = service.get_all_items("/iaa_reports", params=service.where_params(where))
    if len(reports) > 0:
        return reports[0]
    else:
        return None

@bp.route("/by_collection_id/<collection_id>", methods = ["GET"])
@auth.login_required
def get_iia_report_by_collection_id(collection_id):
    where = {
        "collection_id": collection_id
    }
    resp = service.get("iaa_reports", params=service.where_params(where))
    if not resp.ok:
        abort(resp.status_code)
    return service.convert_response(resp)

def update_iaa_report_by_collection_id(collection_id: str) -> bool:
    logger.info("Updating IAA report for collection " + collection_id)
    new_report = iaa_service.getIAAReportForCollection(collection_id)
    if new_report:
        current_report = get_current_report(collection_id)
        if current_report != None:
            headers = {"If-Match": current_report["_etag"]}
            return service.patch(["iaa_reports", current_report["_id"]], json = new_report, headers = headers).ok
        else:
            return service.post("iaa_reports", json = new_report).ok
    else:
        return jsonify(False)

@bp.route("/by_collection_id/<collection_id>", methods=["POST"])
@auth.login_required
def create_iaa_report_by_collection_id(collection_id):
    return jsonify(update_iaa_report_by_collection_id(collection_id))


def init_app(app):
    app.register_blueprint(bp)

