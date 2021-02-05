# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import sys

import click
from flask import abort
from flask.cli import with_appcontext

from . import service
from ..auth import password as authpassword
from .. import models

def get_all_users():
    return service.get_all_items("/users")

def get_user(user_id):
    # getting by ID in the normal way doesn't work sometimes
    items = service.get_all_items("users", params=service.params({
        "where": {
            "_id": user_id
        }
    }))
    if items and len(items) == 1:
        return items[0]
    else:
        abort(404)

def get_user_by_email(email):
    where = {
        "email": email
    }
    users = service.get_all_items("/users", params=service.where_params(where))
    if len(users) > 0:
        return users[0]
    else:
        return None

def get_user_by_id_or_email(username):
    try:
        return get_user(username)
    except:
        return get_user_by_email(username)

def get_user_details(user_id):
    user = get_user(user_id)
    return models.UserDetails(first_name = user["firstname"], last_name = user["lastname"],
                              description = user["description"])

def update_user(user_id: str, details: models.UserDetails):
    current = get_user(user_id)
    if details.first_name != None:
        current["firstname"] = details.first_name
    if details.last_name != None:
        current["lastname"] = details.last_name
    if details.description != None:
        current["description"] = details.description
    etag = current["_etag"]
    service.remove_nonupdatable_fields(current)
    resp = service.put(["users", user_id], json = current, headers = {"If-Match": etag})
    if not resp.ok:
        abort(resp.status_code, resp.content)
    return resp.json()

@click.command("print-users")
@with_appcontext
def print_users_command():
    click.echo("Using data backend {}".format(service.url("")))
    for user in get_all_users():
        click.echo("* email={} id={}{}\n  {} {}: {}".format(user["email"], user["_id"],
            " (admin)" if "role" in user and "administrator" in user["role"] else "",
            user["firstname"], user["lastname"],
            user["description"]))

@click.command("add-admin")
@click.argument("user_id")
@click.argument("username")
@click.argument("password")
@with_appcontext
def add_admin_command(user_id, username, password):
    try:
        get_user(user_id)
        click.echo("User with ID {} already exists.".format(user_id))
        return
    except:
        pass
    user = {
        "_id": user_id,
        "email": username,
        "passwdhash": authpassword.hash_password(password),
        "firstname": "New",
        "lastname": "Administrator",
        "description": "New administrator account.",
        "role": ["administrator"]
    }
    click.echo("Putting to {}: {}".format(service.url("users"), user))
    resp = service.post("users", json = user)
    if not resp.ok:
        abort(resp.status_code)

def set_user_password_by_id(user_id, password):
    user = get_user(user_id)
    user["passwdhash"] = authpassword.hash_password(password)
    etag = user["_etag"]
    service.remove_nonupdatable_fields(user)
    headers = {"If-Match": etag}
    print("Putting to {}: {}".format(service.url(["users", user["_id"]]), user))
    sys.stdout.flush()
    resp = service.put(["users", user["_id"]], json = user, headers = headers)
    if not resp.ok:
        abort(resp.status_code)

@click.command("set-user-password")
@click.argument("username")
@click.argument("password")
@with_appcontext
def set_user_password(username, password):
    click.echo("Using data backend {}".format(service.url("")))
    user = get_user_by_id_or_email(username)
    if user == None:
        click.echo("Unable to find user with username {}\nPlease pass in email or ID.".format(username))
        return
    user["passwdhash"] = authpassword.hash_password(password)
    etag = user["_etag"]
    service.remove_nonupdatable_fields(user)
    headers = {"If-Match": etag}
    click.echo("Putting to {}: {}".format(service.url(["users", user["_id"]]), user))
    resp = service.put(["users", user["_id"]], json = user, headers = headers)
    if not resp.ok:
        click.echo("Failure! {}".format(resp))
    else:
        click.echo("Success!")

@click.command("reset-user-passwords")
@with_appcontext
def reset_user_passwords():
    click.echo("Using data backend {}".format(service.url("")))
    click.echo("Resetting all user passwords to the user's email.")
    for user in get_all_users():
        user["passwdhash"] = authpassword.hash_password(user["email"])
        etag = user["_etag"]
        service.remove_nonupdatable_fields(user)
        headers = {"If-Match": etag}
        click.echo("Putting to {}: {}".format(service.url("users", user["_id"]), user))
        resp = service.put(["users", user["_id"]], json = user, headers = headers)
        if not resp.ok:
            click.echo("Failure! {}".format(resp))
        else:
            click.echo("Success!")
