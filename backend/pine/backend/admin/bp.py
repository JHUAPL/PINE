# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

from flask import Blueprint, jsonify, request, Response
import requests
from werkzeug import exceptions

from .. import auth
from ..auth import password
from ..data import service, users

bp = Blueprint("admin", __name__, url_prefix = "/admin")

@bp.route("/users", methods = ["GET"])
@auth.admin_required
def get_users():
    """
    Get the list of all users' details (id, email, and password hash)
    :return: str
    """
    return jsonify(users.get_all_users())

@bp.route("/users/<user_id>", methods = ["GET"])
@auth.admin_required
def get_user(user_id):
    """
    Given a user_id, return the user's details (id, email, and password hash)
    :param user_id: str
    :return: str
    """
    return jsonify(users.get_user(user_id))

@bp.route("/users/<user_id>/password", methods = ["POST", "PUT", "PATCH"])
@auth.admin_required
def update_user_password(user_id):
    """
    Change the password hash stored in the database for the given user to a newly calculated password hash derived from
    the password provided in the json body of this request.
    :param user_id:
    :return: Response
    """
    if not request.is_json:
        raise exceptions.BadRequest()
    body = request.get_json()
    user = users.get_user(user_id)
    etag = user["_etag"]
    service.remove_nonupdatable_fields(user)
    user["passwdhash"] = password.hash_password(body["passwd"])
    resp = service.put("users/" + user_id, json = user, headers = {"If-Match": etag})
    return service.convert_response(resp)

@bp.route("/users/<user_id>", methods = ["PUT", "PATCH"])
@auth.admin_required
def update_user(user_id):
    """
    Change the details stored in the database for the given user to those provided in the json body of this request.
    :param user_id: str
    :return: Response
    """
    if not request.is_json:
        raise exceptions.BadRequest()
    body = request.get_json()
    etag = body["_etag"]
    service.remove_nonupdatable_fields(body)
    resp = service.put("users/" + user_id, json = body, headers = {"If-Match": etag})
    return service.convert_response(resp)

@bp.route("/users", methods = ["POST"])
@auth.admin_required
def add_user():
    """
    Add a new user to PINE, with the details provided in the json body of this request (id, email, and password hash).
    This method will calculate and store a password hash based upon the provided password
    :return: Response
    """
    if not request.is_json:
        raise exceptions.BadRequest()
    body = request.get_json()

    # first check that username and email are not already in user
    if not "id" in body or not body["id"]:
        raise exceptions.BadRequest(description = "Missing id in body JSON data.")
    try:
        user = users.get_user(body["id"])
        if user != None:
            raise exceptions.Conflict(description = "User with id {} already exists.".format(body["username"]))
    except exceptions.NotFound: pass
    if not "email" in body or not body["email"]:
        raise exceptions.BadRequest(description = "Missing email in body JSON data.")
    user = users.get_user_by_email(body["email"])
    if user != None:
        raise exceptions.Conflict(description = "User with email {} already exists.".format(body["email"]))

    # replace the password with a hash
    if not "passwd" in body or not body["passwd"]:
        raise exceptions.BadRequest(description = "Missing passwd in body JSON data.")
    body["passwdhash"] = password.hash_password(body["passwd"])
    del body["passwd"]
    
    body["_id"] = body["id"]
    del body["id"]
    if body["description"] == None:
        del body["description"]
    
    # post to data server
    resp = service.post("users", json = body)
    return service.convert_response(resp)

@bp.route("/users/<user_id>", methods = ["DELETE"])
@auth.admin_required
def delete_user(user_id):
    """
    Delete the user matching the given user_id
    :param user_id: str
    :return: Response
    """
    # make sure you're not deleting the logged in user
    if user_id == auth.get_logged_in_user()["id"]:
        return jsonify({"success": False, "error": "Cannot delete currently logged in user."}), exceptions.Conflict.code
    
    # TODO if that user is logged in, force log them out
    
    # delete user
    user = users.get_user(user_id)
    headers = {"If-Match": user["_etag"]}
    return service.convert_response(service.delete("users/" + user_id, headers = headers))

@bp.route("/system/export", methods = ["GET"])
@auth.admin_required
def system_export():
    """
    Export the contents of the database as a zip file
    :return: Response
    """
    resp = service.convert_response(service.get("system/export"))
    resp.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
    return resp

@bp.route("/system/import", methods = ["PUT", "POST"])
@auth.admin_required
def system_import():
    """
    Import the contents of the data provided in the request body to the database
    :return: Response
    """
    return service.convert_response(
        requests.request(request.method, service.url("system", "import"), data = request.get_data(),
                         headers = request.headers))

def init_app(app):
    app.register_blueprint(bp)
