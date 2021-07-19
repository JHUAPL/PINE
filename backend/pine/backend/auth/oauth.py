# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import abc
import logging
import sys
import traceback
import urllib

from authlib.integrations.flask_client import OAuth
from flask import current_app, jsonify, redirect, request, Response, session
import jwt
from overrides import overrides
from werkzeug import exceptions

from . import bp
from .. import log, models

LOGGER = logging.getLogger(__name__)

class OAuthUser(models.AuthUser):
    
    def __init__(self, data, id_field, display_field=None):
        super(OAuthUser, self).__init__()
        self.data = data
        self.id_field = id_field
        if display_field:
            self.display_field = display_field
        else:
            self.display_field = id_field
        
    @property
    @overrides
    def id(self):
        return self.data[self.id_field]
    
    @property
    @overrides
    def username(self):
        return self.data[self.id_field]

    @property
    @overrides
    def display_name(self):
        return self.data[self.display_field]

    @property
    @overrides
    def is_admin(self):
        return False

class OAuthModule(bp.AuthModule):
    
    def __init__(self, app, bp, secret):
        super(OAuthModule, self).__init__(app, bp)
        self.oauth = OAuth()
        self.oauth.init_app(app)
        self.app = self.register_oauth(self.oauth, app)
        self.secret = secret
        bp.route("/login", methods=["POST"])(self.login)
        bp.route("/authorize", methods=["GET"])(self.authorize_get)
        bp.route("/authorize", methods=["POST"])(self.authorize_post)

    @abc.abstractmethod
    def register_oauth(self, oauth, app):
        pass

    @abc.abstractmethod
    def get_login_form_button_text(self):
        pass

    @overrides
    def is_flat(self) -> bool:
        return True
    
    @overrides
    def can_manage_users(self) -> bool:
        return False

    @overrides
    def get_login_form(self) -> models.LoginForm:
        return models.LoginForm([], self.get_login_form_button_text())

    def make_user(self, decoded: dict) -> OAuthUser:
        return OAuthUser(decoded, id_field="sub")

    def login(self) -> Response:
        if "return_to" in request.args:
            redirect = self.app.authorize_redirect(request.args.get("return_to"), response_type = "token")
        else:
            redirect = self.app.authorize_redirect(response_type = "token")
        return jsonify(redirect.headers["Location"])

    def _authorize(self, authorization_response):
        try:
            token = self.app.fetch_access_token(authorization_response = authorization_response)
        except Exception as e:
            traceback.print_exc()
            sys.stderr.flush()
            raise exceptions.SecurityError(description = str(e))
        access_token = token["access_token"]
        try:
            decoded = jwt.decode(access_token, self.secret, verify = False)
            decoded = jwt.decode(access_token, self.secret, verify = True, audience = decoded["aud"])
        except jwt.exceptions.InvalidTokenError as e:
            traceback.print_exc()
            sys.stderr.flush()
            raise exceptions.SecurityError(description = str(e))
        LOGGER.info("Decoded and validated token: {}".format(decoded))
        session["auth"] = {
            "user": self.make_user(decoded).to_dict(),
            "user_data": decoded,
            "token": token
        }
        log.access_flask_login()
        return jsonify(self.get_logged_in_user())

    def authorize_post(self):
        body = request.get_json()
        if not body:
            raise exceptions.BadRequest()
        LOGGER.info("Received authorize POST with body {}".format(body))
        authorization_response = request.full_path + "#" + urllib.parse.urlencode(body)
        return self._authorize(authorization_response)

    def authorize_get(self):
        LOGGER.info("Received authorize GET with fragment {}".format(request.args.get("fragment")))
        authorization_response = request.full_path + "#" + request.args.get("fragment")
        return self._authorize(authorization_response)
