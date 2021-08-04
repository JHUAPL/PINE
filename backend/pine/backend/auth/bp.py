# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import abc
import functools

from flask import Blueprint, current_app, jsonify, request, Response, session
from werkzeug import exceptions

from .. import log, models

CONFIG_AUTH_MODULE_KEY = "AUTH_MODULE"

bp = Blueprint("auth", __name__, url_prefix = "/auth")
module = None

def is_flat():
    return module.is_flat()

def get_logged_in_user():
    return module.get_logged_in_user()

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if module.get_logged_in_user() == None and request.method.lower() != "options":
            raise exceptions.Unauthorized(description = "Must be logged in.")

        return view(*args, **kwargs)

    return wrapped_view

def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        user = module.get_logged_in_user()
        if user == None and request.method.lower() != "options":
            raise exceptions.Unauthorized(description = "Must be logged in.")
        if not user["is_admin"]:
            raise exceptions.Unauthorized(description = "Must be an admin.")

        return view(*args, **kwargs)

    return wrapped_view

@bp.route("/module", methods = ["GET"])
def flask_get_module():
    return jsonify(current_app.config[CONFIG_AUTH_MODULE_KEY])

@bp.route("/flat", methods = ["GET"])
def flask_get_flat() -> Response:
    return jsonify(module.is_flat())

@bp.route("/can_manage_users", methods = ["GET"])
def flask_get_can_manage_users() -> Response:
    return jsonify(module.can_manage_users())

@bp.route("/logged_in_user", methods = ["GET"])
def flask_get_logged_in_user() -> Response:
    return jsonify(module.get_logged_in_user())

@bp.route("/logged_in_user_details", methods = ["GET"])
@login_required
def flask_get_logged_in_user_details() -> Response:
    return jsonify(module.get_logged_in_user_details().to_dict())

@bp.route("/login_form", methods = ["GET"])
def flask_get_login_form() -> Response:
    return jsonify(module.get_login_form().to_dict())

@bp.route("/logout", methods = ["POST"])
@login_required
def flask_post_logout() -> Response:
    user = module.get_logged_in_user()
    module.logout()
    log.access_flask_logout(user)
    return Response(status = 200)

class AuthModule(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, app, bp):
        pass

    @abc.abstractmethod
    def is_flat(self) -> bool:
        pass

    @abc.abstractmethod
    def can_manage_users(self) -> bool:
        pass

    @abc.abstractmethod
    def get_login_form(self) -> models.LoginForm:
        pass

    def get_logged_in_user(self):
        return session["auth"]["user"] if "auth" in session else None

    def get_logged_in_user_details(self) -> models.UserDetails:
        return None

    def logout(self):
        if "auth" in session:
            del session["auth"]

def init_app(app):
    module_config = app.config[CONFIG_AUTH_MODULE_KEY]
    global module
    if module_config == "vegas":
        from . import vegas
        module = vegas.VegasAuthModule(app, bp)
    elif module_config == "eve":
        from . import eve
        module = eve.EveModule(app, bp)
    else:
        raise ValueError("Unknown auth module: {}".format(module_config))
    app.register_blueprint(bp)
