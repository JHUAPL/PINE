# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

from flask import jsonify, request, Response, session
from overrides import overrides
from werkzeug import exceptions

from . import bp, login_required, password
from .. import log, models
from ..data import users

class EveUser(models.AuthUser):
    
    def __init__(self, data):
        super(EveUser, self).__init__()
        self.data = data
        
    @property
    @overrides
    def id(self):
        return self.data["_id"]

    @property
    @overrides
    def username(self):
        return self.data["email"]

    @property
    @overrides
    def display_name(self):
        return "{} {} ({})".format(self.data["firstname"], self.data["lastname"], self.username)

    @property
    @overrides
    def is_admin(self):
        return "administrator" in self.data["role"]

    def get_details(self) -> models.UserDetails:
        return models.UserDetails(self.data["firstname"], self.data["lastname"], self.data["description"])

class EveModule(bp.AuthModule):
    
    def __init__(self, app, bp):
        super(EveModule, self).__init__(app, bp)
        bp.route("/login", methods = ["POST"])(self.login)
        login_required(bp.route("/users", methods = ["GET"])(self.get_all_users))
        login_required(bp.route("/logged_in_user_details", methods = ["POST"])(self.update_user_details))
        login_required(bp.route("/logged_in_user_password", methods = ["POST"])(self.update_user_password))

    @overrides
    def is_flat(self) -> bool:
        return False

    @overrides
    def can_manage_users(self) -> bool:
        return True

    @overrides
    def get_logged_in_user_details(self):
        return EveUser(session["auth"]["user_data"]).get_details()

    def update_user_details(self):
        details = models.UserDetails(**request.get_json())
        ret = users.update_user(self.get_logged_in_user()["id"], details)
        new_user_data = users.get_user(ret["_id"])
        session["auth"] = {
            "user": EveUser(new_user_data).to_dict(),
            "user_data": new_user_data
        }
        return jsonify(True)

    def update_user_password(self):
        body = request.get_json()
        current_password = body["current_password"]
        new_password = body["new_password"]
        valid = password.check_password(current_password, session["auth"]["user_data"]["passwdhash"])
        if not valid:
            raise exceptions.Unauthorized(description = "Current password does not match.")
        users.set_user_password_by_id(self.get_logged_in_user()["id"], new_password)
        return jsonify(True)

    @overrides
    def get_login_form(self) -> models.LoginForm:
        return models.LoginForm([
            models.LoginFormField("username", "Username or email", models.LoginFormFieldType.TEXT),
            models.LoginFormField("password", "Password", models.LoginFormFieldType.PASSWORD)
        ], "Login")

    def login(self) -> Response:
        if not request.json or "username" not in request.json or "password" not in request.json:
            raise exceptions.BadRequest(description = "Missing username and/or password.")
        username = request.json["username"]
        passwd = request.json["password"]
        try:
            user = users.get_user(username)
        except exceptions.HTTPException:
            try:
                user = users.get_user_by_email(username)
                if not user:
                    raise exceptions.Unauthorized(description = "User \"{}\" doesn't exist.".format(username))
            except exceptions.HTTPException:
                raise exceptions.Unauthorized(description = "User \"{}\" doesn't exist.".format(username))
        if not "passwdhash" in user or not user["passwdhash"]:
            raise exceptions.Unauthorized(description = "Your first-time password needs to be set by an administrator.")
        valid = password.check_password(passwd, user["passwdhash"])
        if not valid:
            raise exceptions.Unauthorized(description = "Incorrect password for user \"{}\".".format(username))
        session["auth"] = {
            "user": EveUser(user).to_dict(),
            "user_data": user
        }
        log.access_flask_login()
        return jsonify(self.get_logged_in_user())

    def get_all_users(self):
        ret = []
        for user in users.get_all_users():
            ret.append(EveUser(user).to_dict())
        return jsonify(ret)
