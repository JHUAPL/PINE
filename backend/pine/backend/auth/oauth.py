# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import abc
import traceback

from authlib.integrations.flask_client import OAuth
from flask import current_app, jsonify, redirect, request, Response, session
import jwt
from overrides import overrides
from werkzeug import exceptions

from . import bp
from .. import log, models

#{'sub': 'lglende1', 'aud': 'NLP Platform', 'subject': 'lglende1', 'iss': 'https://slife.jh.edu', 'token_type': 'access_token', 'exp': 1563587426, 'expires_in': 3600, 'iat': 1563583826, 'email': 'lglende1@jhu.edu', 'client_id': '1976d9d4-be86-44ce-aa0f-c5a4b295c701'}

class OAuthUser(models.AuthUser):
    
    def __init__(self, data):
        super(OAuthUser, self).__init__()
        self.data = data
        
    @property
    @overrides
    def id(self):
        return self.data["subject"]
    
    @property
    @overrides
    def username(self):
        return self.data["subject"]

    @property
    @overrides
    def display_name(self):
        return self.data["subject"]

    @property
    @overrides
    def is_admin(self):
        return False

class OAuthModule(bp.AuthModule):
    
    def __init__(self, app, bp):
        super(OAuthModule, self).__init__(app, bp)
        self.oauth = OAuth()
        self.oauth.init_app(app)
        self.app = self.register_oauth(self.oauth, app)
        bp.route("/login", methods = ["POST"])(self.login)
        bp.route("/authorize", methods = ["GET"])(self.authorize)

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

    def login(self) -> Response:
        if "return_to" in request.args:
            redirect = self.app.authorize_redirect(request.args.get("return_to"), response_type = "token")
        else:
            redirect = self.app.authorize_redirect(response_type = "token")
        return jsonify(redirect.headers["Location"])

    def authorize(self):
        authorization_response = request.full_path + "#" + request.args.get("fragment")
        try:
            token = self.app.fetch_access_token(authorization_response = authorization_response)
        except Exception as e:
            traceback.print_exc()
            raise exceptions.SecurityError(description = str(e))
        access_token = token["access_token"]
        secret = current_app.config["VEGAS_CLIENT_SECRET"]
        try:
            decoded = jwt.decode(access_token, secret, verify = False)
            decoded = jwt.decode(access_token, secret, verify = True, audience = decoded["aud"])
        except jwt.exceptions.InvalidTokenError as e:
            traceback.print_exc()
            raise exceptions.SecurityError(description = str(e))
        session["auth"] = {
            "user": OAuthUser(decoded).to_dict(),
            "user_data": decoded,
            "token": token
        }
        log.access_flask_login()
        return jsonify(self.get_logged_in_user())
