# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import json
import logging
import math
from pprint import pformat, pprint
import sys
import threading
import typing

from flask import abort, current_app, Response
import requests

logger = logging.getLogger(__name__)

PATH_TYPE = typing.Union[typing.List[str], typing.Tuple[str], typing.Set[str], str]
"""Type for paths that can be passed into these messages.  Either a single string, or a list-like
type of strings that is combined with a '/'.
"""

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

    def pformat(self, **kwargs):
        return pformat(self.data, **kwargs)

    def pprint(self):
        self.lock.acquire()
        try:
            pprint(self.data)
            sys.stdout.flush()
        finally:
            self.lock.release()

    def add(self, rest_type: str, path: str, response):
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

def _standardize_path(path: PATH_TYPE, *additional_paths: typing.List[str]) -> typing.List[str]:
    # if you change this, also update client code in pine.client.client module
    if type(path) not in [list, tuple, set]:
        path = [path]
    if additional_paths:
        path += additional_paths
    # for every element in path, split by "/" into a list of paths, then remove empty values
    # "/test" => ["test"], ["/test", "1"] => ["test", "1"], etc.
    return [single_path for subpath in path for single_path in subpath.split("/") if single_path]

def url(path: PATH_TYPE, *additional_paths: typing.List[str]) -> str:
    """Returns a complete URL for the given eve-relative path(s).
    
    :param path: str: eve-relative path (e.g. "collections" or ["collections", id])
    :param additional_paths: str[]: any additional paths to append
    :return: url
    :rtype: str
    """
    return "/".join([current_app.config["EVE_SERVER"].strip("/")] +
                    _standardize_path(path, *additional_paths))


def where_params(where: dict) -> dict:
    """Returns a "where" parameters object that can be passed to eve.
    
    Eve requires that dict parameters be serialized as JSON.
    
    :param where: dict: dictionary of "where" params to pass to eve
    :return: "where" params in eve-appropriate format
    :rtype: dict
    """
    return params({"where": where})

def params(params: dict) -> dict:
    """Returns a parameters object that can be passed to eve.
    
    Eve requires that dict parameters be serialized as JSON.
    
    :param where: dict: dictionary of "where" params to pass to eve
    :return: params in eve-appropriate format
    :rtype: dict
    """
    return {key: json.dumps(value) if type(value) == dict else value for (key, value) in params.items()}


def get(path: PATH_TYPE, **kwargs: dict) -> requests.Response:
    """Wraps requests.get for the given eve-relative path.
    
    :param path: list[str]|str: eve-relative path (e.g. ["collections", id] or "/collections")
    :param **kwargs: dict: any additional arguments to pass to requests.get
    :return: server response
    :rtype: requests.Response
    """
    global PERFORMANCE_HISTORY
    resp = requests.get(url(path), **kwargs)
    PERFORMANCE_HISTORY.add("get", path, resp)
    return resp

def post(path: PATH_TYPE, **kwargs: dict) -> requests.Response:
    """Wraps requests.post for the given eve-relative path.
    
    :param path: list[str]|str: eve-relative path (e.g. ["collections", id] or "/collections")
    :param **kwargs: dict: any additional arguments to pass to requests.post
    :return: server response
    :rtype: requests.Response
    """
    global PERFORMANCE_HISTORY
    resp = requests.post(url(path), **kwargs)
    PERFORMANCE_HISTORY.add("post", path, resp)
    return resp

def put(path: PATH_TYPE, **kwargs: dict) -> requests.Response:
    """Wraps requests.put for the given eve-relative path.
    
    :param path: list[str]|str: eve-relative path (e.g. ["collections", id] or "/collections")
    :param **kwargs: dict: any additional arguments to pass to requests.put
    :return: server response
    :rtype: requests.Response
    """
    global PERFORMANCE_HISTORY
    resp = requests.put(url(path), **kwargs)
    PERFORMANCE_HISTORY.add("put", path, resp)
    return resp

def delete(path: PATH_TYPE, **kwargs: dict) -> requests.Response:
    """Wraps requests.delete for the given eve-relative path.
    
    :param path: list[str]|str: eve-relative path (e.g. ["collections", id] or "/collections")
    :param **kwargs: dict: any additional arguments to pass to requests.delete
    :return: server response
    :rtype: requests.Response
    """
    global PERFORMANCE_HISTORY
    resp = requests.delete(url(path), **kwargs)
    PERFORMANCE_HISTORY.add("delete", path, resp)
    return resp

def patch(path: PATH_TYPE, **kwargs: dict) -> requests.Response:
    """Wraps requests.patch for the given eve-relative path.
    
    :param path: list[str]|str: eve-relative path (e.g. ["collections", id] or "/collections")
    :param **kwargs: dict: any additional arguments to pass to requests.patch
    :return: server response
    :rtype: requests.Response
    """
    global PERFORMANCE_HISTORY
    resp = requests.patch(url(path), **kwargs)
    PERFORMANCE_HISTORY.add("patch", path, resp)
    return resp


def get_item_by_id(path: PATH_TYPE, item_id: str, params: dict = {}) -> dict:
    """Gets a single item by the given ID.
    
    :param path: list[str]|str: eve-relative path (e.g. ["collections", id] or "/collections")
    :param item_id: str: item ID
    :param params: dict: optional additional parameters to send in with GET
    :return: the item as a dict
    :rtype: dict
    """
    resp = get([path, item_id], params=params)
    if not resp.ok:
        abort(resp.status_code, resp.content)
    return resp.json()


def get_all_versions_of_item_by_id(path: PATH_TYPE, item_id: str, params: dict = {}) -> typing.List[dict]:
    """Gets all versions of an item by the given ID.
    
    :param path: list[str]|str: eve-relative path (e.g. ["collections", id] or "/collections")
    :param item_id: str: item ID
    :param params: dict: optional additional arguments to send in with GET
    :return: the items as a list of dicts
    :rtype: list[dict]
    """
    params["version"] = "all"
    resp = get([path, item_id], params=params)
    if not resp.ok:
        abort(resp.status_code, resp.content)
    return resp.json()


def get_all(path: PATH_TYPE, params={}) -> dict:
    """Returns ALL database items, using pagination if needed.  This returns the "normal" eve
    JSON with "_items", "_meta", etc.
    
    :param path: list[str]|str: eve-relative path (e.g. ["collections", id] or "/collections")
    :param params: dict: optional additional parameters to send in with GET
    :return: an eve collections dict with, e.g., _items
    :rtype: dict
    """
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


def get_all_items(path: PATH_TYPE, params={}) -> typing.List[dict]:
    """Returns ALL database items, using pagination if needed.
    
    :param path: list[str]|str: eve-relative path (e.g. ["collections", id] or "/collections")
    :param params: dict: optional additional parameters to send in with GET
    :return: the items as a list of dicts
    :rtype: list[dict]
    """
    return get_all(path, params=params)["_items"]


def convert_response(requests_response: requests.Response) -> Response:
    """Converts a requests response to a flask response.
    
    :param requests_response: requests.Response: response from requests library
    :returns: a flask response
    :rtype: flask.Response
    """
    return Response(requests_response.content,
                    requests_response.status_code,
                    requests_response.raw.headers.items())


def remove_eve_fields(obj: dict, remove_timestamps: bool = True, remove_versions: bool = True) -> None:
    """Removes the fields that eve adds that aren't necessarily relevant to the data.  The object
    that is passed in is modified in-place.
    
    This currently includes: `_etag`, `_links`, `_created` (if `remove_timestamps`), `_updated` (if
    `remove_timestamps`), `_version` (if `remove_versions`), and `_latest_version` (if
    `remove_versions`).
    
    :param obj: dict: the object to modify
    :param remove_timestamps: bool: whether to remove timestamp fields (defaults to `True`)
    :param remove_versions: bool: whether to remove version fields (defaults to `True`)
    """
    fields = ["_etag", "_links"]
    if remove_timestamps: fields += ["_created", "_updated"]
    if remove_versions: fields += ["_version", "_latest_version"]
    for f in fields:
        if f in obj:
            del obj[f]

def remove_nonupdatable_fields(obj: dict) -> None:
    """Removes the non-updatable fields in the given eve object.  This is currently equivalent to
    calling ... with all the default options.
    
    :param obj: dict: the object to modify
    """
    remove_eve_fields(obj)
