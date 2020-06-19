# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import json
import logging
import math
from pprint import pprint
import threading

from flask import abort, current_app, Response
import requests

logger = logging.getLogger(__name__)

class PerformanceHistory(object):

    def __init__(self):
        self.data = {
            "get": {},
            "post": {},
            "put": {},
            "delete": {},
            "patch": {}
        }
        self.lock = threading.Lock()

    def pprint(self):
        self.lock.acquire()
        try:
            pprint(self.data)
        finally:
            self.lock.release()

    def add(self, rest_type, path, response):
        if rest_type not in self.data.keys():
            raise ValueError("Invalid rest type {}".format(rest_type))
        self.lock.acquire()
        try:
            data_type = _standardize_path(path)[0]
            if data_type not in self.data[rest_type]:
                self.data[rest_type][data_type] = {
                    "count": 0,
                    "response_content_size": 0,
                    "request_body_size": 0
                }
            p = self.data[rest_type][data_type]
            p["count"] += 1
            p["response_content_size"] += len(response.content)
            if response.request.body:
                p["request_body_size"] += len(response.request.body)
        finally:
            self.lock.release()

PERFORMANCE_HISTORY = PerformanceHistory()

def _standardize_path(path, *additional_paths):
    if type(path) not in [list, tuple, set]:
        path = [path]
    if additional_paths:
        path += additional_paths
    # for every element in path, split by "/" into a list of paths, then remove empty values
    # "/test" => ["test"], ["/test", "1"] => ["test", "1"], etc.
    return [single_path for subpath in path for single_path in subpath.split("/") if single_path]

def url(path, *additional_paths):
    """Returns a complete URL for the given eve-relative path(s).
    
    :param path: str: eve-relative path (e.g. "collections" or ["collections", id])
    :param additional_paths: str[]: any additional paths to append
    :return: str url
    """
    return "/".join([current_app.config["EVE_SERVER"].strip("/")] +
                    _standardize_path(path, *additional_paths))


def where_params(where):
    """Returns a "where" parameters object that can be passed to eve.
    
    Eve requires that dict parameters be serialized as JSON.
    
    :param where: dict: dictionary of "where" params to pass to eve
    :return: dict "where" params
    """
    return params({"where": where})

def params(params):
    """Returns a parameters object that can be passed to eve.
    
    Eve requires that dict parameters be serialized as JSON.
    
    :param where: dict: dictionary of "where" params to pass to eve
    :return: dict "where" params
    """
    return {key: json.dumps(value) if type(value) == dict else value for (key, value) in params.items()}


def get(path, **kwargs):
    """Wraps requests.get for the given eve-relative path.
    
    :param path: str: eve-relative path (e.g. "collections" or ["collections", id])
    :param **kwargs: dict: any additional arguments to pass to requests.get
    :return: requests.Response
    """
    global PERFORMANCE_HISTORY
    resp = requests.get(url(path), **kwargs)
    PERFORMANCE_HISTORY.add("get", path, resp)
    return resp

def post(path, **kwargs):
    """Wraps requests.post for the given eve-relative path.
    
    :param path: str: eve-relative path (e.g. "collections" or ["collections", id])
    :param **kwargs: dict: any additional arguments to pass to requests.post
    :return: requests.Response
    """
    global PERFORMANCE_HISTORY
    resp = requests.post(url(path), **kwargs)
    PERFORMANCE_HISTORY.add("post", path, resp)
    return resp

def put(path, **kwargs):
    """Wraps requests.put for the given eve-relative path.
    
    :param path: str: eve-relative path (e.g. "collections" or ["collections", id])
    :param **kwargs: dict: any additional arguments to pass to requests.put
    :return: requests.Response
    """
    global PERFORMANCE_HISTORY
    resp = requests.put(url(path), **kwargs)
    PERFORMANCE_HISTORY.add("put", path, resp)
    return resp

def delete(path, **kwargs):
    """Wraps requests.delete for the given eve-relative path.
    
    :param path: str: eve-relative path (e.g. "collections" or ["collections", id])
    :param **kwargs: dict: any additional arguments to pass to requests.delete
    :return: requests.Response
    """
    global PERFORMANCE_HISTORY
    resp = requests.delete(url(path), **kwargs)
    PERFORMANCE_HISTORY.add("delete", path, resp)
    return resp

def patch(path, **kwargs):
    """Wraps requests.patch for the given eve-relative path.
    
    :param path: str: eve-relative path (e.g. "collections" or ["collections", id])
    :param **kwargs: dict: any additional arguments to pass to requests.patch
    :return: requests.Response
    """
    global PERFORMANCE_HISTORY
    resp = requests.patch(url(path), **kwargs)
    PERFORMANCE_HISTORY.add("patch", path, resp)
    return resp


def get_items(path, params={}):
    resp = get(path, params=params)
    if not resp.ok:
        abort(resp.status_code, resp.content)
    return resp.json()["_items"]


def get_item_by_id(path, item_id, params={}):
    resp = get([path, item_id], params=params)
    if not resp.ok:
        abort(resp.status_code, resp.content)
    return resp.json()


def get_all_versions_of_item_by_id(path, item_id, params = {}):
    params["version"] = "all"
    resp = get([path, item_id], params=params)
    if not resp.ok:
        abort(resp.status_code, resp.content)
    return resp.json()


def get_all_using_pagination(path, params):
    resp = get(path, params=params)
    if not resp.ok:
        abort(resp.status_code)
    body = resp.json()
    if "_meta" not in body:
        return body
    all_items = {"_items": []}
    all_items["_items"] += body["_items"]

    page = body["_meta"]["page"]
    total_pages = math.ceil(body["_meta"]["total"] / body["_meta"]["max_results"])

    while page < total_pages:
        page += 1
        params["page"] = page
        resp = get(path, params=params)
        if not resp.ok:
            abort(resp.status_code)
        body = resp.json()
        all_items["_items"] += body["_items"]
        page = body["_meta"]["page"]
        total_pages = math.ceil(body["_meta"]["total"] / body["_meta"]["max_results"])

    return all_items


def convert_response(requests_response):
    return Response(requests_response.content,
                    requests_response.status_code,
                    requests_response.raw.headers.items())


def remove_eve_fields(obj, remove_timestamps = True, remove_versions = True):
    fields = ["_etag", "_links"]
    if remove_timestamps: fields += ["_created", "_updated"]
    if remove_versions: fields += ["_version", "_latest_version"]
    for f in fields:
        if f in obj:
            del obj[f]

def remove_nonupdatable_fields(obj):
    remove_eve_fields(obj)
