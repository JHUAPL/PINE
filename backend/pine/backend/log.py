# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import enum
import json
import logging.config
import os
import typing

# make sure this package has been installed
import pythonjsonlogger

CONFIG_FILE_ENV = "PINE_LOGGING_CONFIG_FILE"

ACCESS_LOGGER_NAME = "pine.access"
ACCESS_LOGGER = None

class Action(enum.Enum):
    LOGIN = enum.auto()
    LOGOUT = enum.auto()
    CREATE_COLLECTION = enum.auto()
    VIEW_DOCUMENT = enum.auto()
    ADD_DOCUMENT = enum.auto()
    ADD_DOCUMENTS = enum.auto()
    ANNOTATE_DOCUMENT = enum.auto()
    ANNOTATE_DOCUMENTS = enum.auto()

def setup_logging():
    if CONFIG_FILE_ENV not in os.environ:
        logging.basicConfig()
        logging.warn("Using basic configuration; set {} environment variable to use file.".format(CONFIG_FILE_ENV))
        return
    file = os.environ[CONFIG_FILE_ENV]
    if os.path.isfile(file):
        with open(file, "r") as f:
            logging.config.dictConfig(json.load(f))
        logging.getLogger(__name__).info("Set logging configuration from file {}".format(file))

def get_flask_request_info():
    from flask import request
    info = {
        "ip": request.remote_addr,
        "path": request.full_path
    }
    ua = request.headers.get("User-Agent", None)
    if ua: info["user-agent"] = ua
    return info

def get_flask_logged_in_user():
    from .auth import bp
    user = bp.get_logged_in_user()
    return {
        "id": user["id"],
        "username": user["username"]
    }

###############

def access_flask_login():
    access(Action.LOGIN, get_flask_logged_in_user(), get_flask_request_info(), None)

def access_flask_logout(user: dict):
    access(Action.LOGOUT, {"id": user["id"], "username": user["username"]}, get_flask_request_info(), None)

def access_flask_add_collection(collection: dict):
    extra_info = {
        "collection_id": collection["_id"]
    }
    if "metadata" in collection:
        extra_info["collection_metadata"] = collection["metadata"]
        for k in list(extra_info["collection_metadata"].keys()):
            if not extra_info["collection_metadata"][k]:
                del extra_info["collection_metadata"][k]
    access(Action.CREATE_COLLECTION, get_flask_logged_in_user(), get_flask_request_info(), None, **extra_info)

def access_flask_view_document(document: dict):
    extra_info = {
        "document_id": document["_id"]
    }
    if "metadata" in document:
        extra_info["document_metadata"] = document["metadata"]
    access(Action.VIEW_DOCUMENT, get_flask_logged_in_user(), get_flask_request_info(), None, **extra_info)

def access_flask_add_document(document: dict):
    extra_info = {
        "document_id": document["_id"]
    }
    if "metadata" in document:
        extra_info["document_metadata"] = document["metadata"]
    access(Action.ADD_DOCUMENT, get_flask_logged_in_user(), get_flask_request_info(), None, **extra_info)

def access_flask_add_documents(documents: typing.List[dict]):
    doc_info = []
    for document in documents:
        i = {"id": document["_id"]}
        if "metadata" in document: i["metadata"] = document["metadata"]
        doc_info.append(i)
    extra_info = {
        "documents": doc_info
    }
    access(Action.ADD_DOCUMENTS, get_flask_logged_in_user(), get_flask_request_info(), None, **extra_info)

def access_flask_annotate_document(annotation):
    extra_info = {
        "document_id": annotation["document_id"],
        "annotation_id": annotation["_id"]
    }
    access(Action.ANNOTATE_DOCUMENT, get_flask_logged_in_user(), get_flask_request_info(), None, **extra_info)

def access_flask_annotate_documents(annotations: typing.List[dict]):
    extra_info = {
        "document_ids": [annotation["document_id"] for annotation in annotations],
        "annotation_ids": [annotation["_id"] for annotation in annotations]
    }
    access(Action.ANNOTATE_DOCUMENTS, get_flask_logged_in_user(), get_flask_request_info(), None, **extra_info)

###############

def access(action, user, request_info, message, **extra_info):
    global ACCESS_LOGGER
    if not ACCESS_LOGGER:
        ACCESS_LOGGER = logging.getLogger(ACCESS_LOGGER_NAME)
    m = {
        "user": user,
        "action": action.name,
        "request": request_info
    }
    if message: m["message"] = message
    ACCESS_LOGGER.critical(m, extra=extra_info)
