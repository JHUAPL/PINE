# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

"""PINE client classes module.
"""

import abc
import json
import logging
import typing

from overrides import overrides
import pymongo
import requests

from . import exceptions, models, password

def _standardize_path(path: str, *additional_paths: typing.List[str]) -> typing.List[str]:
    r"""Standardize path(s) into a list of path components.
    
    :param path: relative path, e.g. ``"users"``
    :type path: str
    :param \*additional_paths: any additional path components in a list
    :type \*additional_paths: list(str), optional
    
    :return: the standardized path components in a list
    :rtype: list(str)
    """
    # if you change this, also update backend module pine.backend.data.service
    if type(path) not in [list, tuple, set]:
        path = [path]
    if additional_paths:
        path += additional_paths
    # for every element in path, split by "/" into a list of paths, then remove empty values
    # "/test" => ["test"], ["/test", "1"] => ["test", "1"], etc.
    return [single_path for subpath in path for single_path in subpath.split("/") if single_path]

class BaseClient(object):
    """Base class for a client using a REST interface.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, base_uri: str, name: str = None):
        """Constructor.
        
        :param base_uri: the base URI for the server, e.g. ``"http://localhost:5000"``
        :type base_uri: str
        :param name: optional human-readable name for the server, defaults to None
        :type name: str, optional
        """
        self.base_uri: str = base_uri.strip("/")
        """The server's base URI.
        
        :type: str
        """
        self.session: requests.Session = None
        """The currently open session, or ``None``.
        
        :type: requests.Session
        """
        self.name: str = name
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def is_valid(self) -> bool:
        """Returns whether this client and its connection(s) are valid.
        
        :return: whether this client and its connection(s) are valid
        :rtype: bool
        """
        raise NotImplementedError()

    def uri(self, path: str, *additional_paths: typing.List[str]) -> str:
        r"""Makes a complete URI from the given path(s).
        
        :param path: relative path, e.g. ``"users"``
        :type path: str
        :param \*additional_paths: any additional path components
        :type \*additional_paths: list(str), optional
        
        :return: the complete, standardized URI including the base URI, e.g. ``"http://localhost:5000/users"``
        :rtype: str
        """
        return "/".join([self.base_uri] + _standardize_path(path, *additional_paths))

    def _req(self, method: str, path: str, *additional_paths: typing.List[str], **kwargs) -> requests.Response:
        r"""Makes a :py:mod:`requests` call, checks for errors, and returns the response.
        
        :param method: REST method (``"get"``, ``"post"``, etc.)
        :type method: str
        :param path: relative path, e.g. ``"users"``
        :type path: str
        :param \*additional_paths: any additional path components
        :type \*additional_paths: list(str), optional
        :param \**kwargs: any additional kwargs to send to :py:mod:`requests`
        :type \**kwargs: dict
        
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :return: the :py:mod:`requests` :py:class:`requests.Response` object
        :rtype: requests.Response
        """
        uri = self.uri(path, *additional_paths)
        self.logger.debug("{} {}".format(method.upper(), uri))
        if self.session:
            resp = self.session.request(method, uri, **kwargs)
        else:
            resp = requests.request(method, uri, **kwargs)
        if not resp.ok:
            uri = "\"/" + "/".join(_standardize_path(path, *additional_paths)) + "\""
            raise exceptions.PineClientHttpException("{}".format(method.upper()),
                                                 "{} {}".format(self.name, uri) if self.name else uri,
                                                 resp)
        return resp

    def get(self, path: str, *additional_paths: typing.List[str], **kwargs) -> requests.Response:
        r"""Makes a :py:mod:`requests` ``GET`` call, checks for errors, and returns the response.
        
        :param path: relative path, e.g. ``"users"``
        :type path: str
        :param \*additional_paths: any additional path components
        :type \*additional_paths: list(str), optional
        :param \**kwargs: any additional kwargs to send to :py:mod:`requests`
        :type \**kwargs: dict
        
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :return: the :py:mod:`requests` :py:class:`Response <requests.Response>` object
        :rtype: requests.Response
        """
        return self._req("GET", path, *additional_paths, **kwargs)

    def put(self, path: str, *additional_paths: typing.List[str], **kwargs) -> requests.Response:
        r"""Makes a :py:mod:`requests` ``PUT`` call, checks for errors, and returns the response.
        
        :param path: relative path, e.g. ``"users"``
        :type path: str
        :param \*additional_paths: any additional path components
        :type \*additional_paths: list(str), optional
        :param \**kwargs: any additional kwargs to send to :py:mod:`requests`
        :type \**kwargs: dict
        
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :return: the :py:mod:`requests` :py:class:`Response <requests.Response>` object
        :rtype: requests.Response
        """
        return self._req("PUT", path, *additional_paths, **kwargs)

    def patch(self, path: str, *additional_paths: typing.List[str], **kwargs) -> requests.Response:
        r"""Makes a :py:mod:`requests` ``PATCH`` call, checks for errors, and returns the response.
        
        :param path: relative path, e.g. ``"users"``
        :type path: str
        :param \*additional_paths: any additional path components
        :type \*additional_paths: list(str), optional
        :param \**kwargs: any additional kwargs to send to :py:mod:`requests`
        :type \**kwargs: dict
        
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :return: the :py:mod:`requests` :py:class:`Response <requests.Response>` object
        :rtype: requests.Response
        """
        return self._req("PATCH", path, *additional_paths, **kwargs)

    def post(self, path: str, *additional_paths: typing.List[str], **kwargs) -> requests.Response:
        r"""Makes a :py:mod:`requests` ``POST`` call, checks for errors, and returns the response.
        
        :param path: relative path, e.g. ``"users"``
        :type path: str
        :param \*additional_paths: any additional path components
        :type \*additional_paths: list(str), optional
        :param \**kwargs: any additional kwargs to send to :py:mod:`requests`
        :type \**kwargs: dict
        
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :return: the :py:mod:`requests` :py:class:`Response <requests.Response>` object
        :rtype: requests.Response
        """
        return self._req("POST", path, *additional_paths, **kwargs)


class EveClient(BaseClient):
    """A client to access Eve and, optionally, its underlying MongoDB instance.
    """

    DEFAULT_DBNAME: str = "pmap_nlp"
    """The default DB name used by PINE.
    
    :type: str
    """

    def __init__(self, eve_base_uri: str, mongo_base_uri: str = None, mongo_dbname: str = DEFAULT_DBNAME):
        """Constructor.
        
        :param eve_base_uri: the base URI for the eve server, e.g. ``"http://localhost:5001"``
        :type eve_base_uri: str
        :param mongo_base_uri: the base URI for the mongodb server, e.g. ``"mongodb://localhost:27018"``, defaults to ``None``
        :type mongo_base_uri: str, optional
        :param mongo_dbname: the DB name that PINE uses, defaults to ``"pmap_nlp"``
        :type mongo_dbname: str, optional
        """
        super().__init__(eve_base_uri, name="eve")
        self.mongo_base_uri: str = mongo_base_uri
        """The base URI for the MongoDB server.
        
        :type: str
        """
        self.mongo: pymongo.MongoClient = pymongo.MongoClient(mongo_base_uri) if mongo_base_uri else None
        """The :py:class:`pymongo.mongo_client.MongoClient` instance.
        
        :type: pymongo.mongo_client.MongoClient
        """
        self.mongo_db: pymongo.database.Database = self.mongo[mongo_dbname] if self.mongo and mongo_dbname else None
        """The :py:class:`pymongo.database.Database` instance.
        
        :type: pymongo.database.Database
        """

    @overrides
    def is_valid(self) -> bool:
        if self.mongo_base_uri:
            try:
                if not pymongo.MongoClient(self.mongo_base_uri, serverSelectionTimeoutMS=1).server_info():
                    self.logger.error("Unable to connect to MongoDB")
                    return False
            except:
                self.logger.error("Unable to connect to MongoDB", exc_info=True)
                return False
        try:
            self.ping()
        except:
            self.logger.error("Unable to ping eve", exc_info=True)
            return False
        return True

    def ping(self) -> typing.Any:
        """Pings the eve server and returns the result.
        
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: the JSON response from the server (probably ``"pong"``)
        """
        return self.get("system/ping").json()

    def about(self) -> dict:
        """Returns the 'about' dict from the server.
        
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: the JSON response from the server
        :rtype: dict
        """
        return self.get("about").json()

    def get_resource(self, resource: str, resource_id: str) -> dict:
        """Gets a resource from eve by its ID.
        
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: the JSON object response from the server
        :rtype: dict
        """
        return self.get(resource, resource_id).json()

    def _add_or_replace_resource(self, resource: str, obj: dict, valid_fn: typing.Callable[[dict, typing.Callable[[str], None]], bool] = None) -> str:
        """Adds or replaces the given resource.
        
        :param resource: the resource type, e.g. ``"users"``
        :type resource: str
        :param obj: the resource object
        :type obj: dict
        :param valid_fn: a function to validate the resource object, defaults to ``None``
        :type valid_fn: function, optional
        
        :raises exceptions.PineClientValueException: if a valid_fn is passed in and the object fails
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: the ID of the added/replaced resource
        :rtype: str
        """
        if valid_fn and not valid_fn(obj):
            raise exceptions.PineClientValueException(obj, resource)
        if models.ID_FIELD in obj:
            try:
                res = self.get_resource(resource, obj[models.ID_FIELD])
            except exceptions.PineClientHttpException as e:
                if e.resp.status_code == 404:
                    return self.post(resource, obj).json()[models.ID_FIELD]
                else:
                    raise e
            return self.put(resource, obj[models.ID_FIELD], json=obj, headers={"If-Match": res["_etag"]}).json()[models.ID_FIELD]
        else:
            return self.post(resource, obj).json()[models.ID_FIELD]

    def _add_resources(self, resource: str, objs: typing.List[dict], valid_fn: typing.Callable[[dict, typing.Callable[[str], None]], bool] = None, replace_if_exists: bool = False):
        """Tries to add all the resource objects at once, optionally falling back to individual replacement if that fails.
        
        :param resource: the resource type, e.g. ``"users"``
        :type resource: str
        :param objs: the resource objects
        :type objs: list(dict)
        :param valid_fn: a function to validate the resource object, defaults to ``None``
        :type valid_fn: function, optional
        :param replace_if_exists: whether to replace the resource with the given value if it already exists on the server, defaults to ``False``
        :type replace_if_exists: bool, optional
        
        :raises exceptions.PineClientValueException: if a valid_fn is passed in and any of the objects fails
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: the IDs of the added resources
        :rtype: list(str)
        """
        if objs == None:
            return []
        if valid_fn:
            for obj in objs:
                if not valid_fn(obj, self.logger.warn):
                    raise exceptions.PineClientValueException(obj, resource)
        try:
            resp = self.post(resource, json=objs)
            return [item[models.ID_FIELD] for item in resp.json()[models.ITEMS_FIELD]]
        except exceptions.PineClientHttpException as e:
            if e.resp.status_code == 409 and replace_if_exists:
                return [self.add_or_replace_resource(resource, obj, valid_fn) for obj in objs]
            else:
                raise e

    def add_users(self, users: typing.List[dict], replace_if_exists=False) -> typing.List[str]:
        """Adds the given users.
        
        :param users: the user objects
        :type users: list(dict)
        :param replace_if_exists: whether to replace the resource with the given value if it already exists on the server, defaults to ``False``
        :type replace_if_exists: bool, optional
        
        :raises exceptions.PineClientValueException: if any of the user objects are not valid, see :py:func:`.models.is_valid_eve_user`
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: the IDs of the added users
        :rtype: list(str)
        """
        for user in users:
            if "password" in user:
                user["passwdhash"] = password.hash_password(user["password"])
                del user["password"]
        return self._add_resources("users", users, valid_fn=models.is_valid_eve_user, replace_if_exists=replace_if_exists)

    def get_users(self):
        """Gets all users.
        
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: all the users
        :rtype: list(dict)
        """
        return self.get("users").json()[models.ITEMS_FIELD]

    def add_pipelines(self, pipelines: typing.List[dict], replace_if_exists=False) -> typing.List[str]:
        """Adds the given pipelines.
        
        :param pipelines: the pipeline objects
        :type pipelines: list(dict)
        :param replace_if_exists: whether to replace the resource with the given value if it already exists on the server, defaults to ``False``
        :type replace_if_exists: bool, optional
        
        :raises exceptions.PineClientValueException: if any of the pipeline objects are not valid, see :py:func:`.models.is_valid_eve_pipeline`
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: the IDs of the added pipelines
        :rtype: list(str)
        """
        return self._add_resources("pipelines", pipelines, valid_fn=models.is_valid_eve_pipeline, replace_if_exists=replace_if_exists)


class PineClient(BaseClient):
    """A client to access PINE (more specifically: the backend).
    """

    def __init__(self, backend_base_uri: str):
        """Constructor.
        
        :param backend_base_uri: the base URI for the backend server, e.g. ``"http://localhost:5000"``
        :type backend_base_uri: str
        """
        super().__init__(backend_base_uri)

    @overrides
    def is_valid(self) -> bool:
        try:
            self.ping()
            return True
        except:
            self.logger.error("Unable to ping PINE backend", exc_info=True)
            return False

    def ping(self) -> typing.Any:
        """Pings the backend server and returns the result.
        
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: the JSON response from the server (probably ``"pong"``)
        """
        return self.get("ping").json()

    def about(self) -> dict:
        """Returns the 'about' dict from the server.
        
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: the JSON response from the server
        :rtype: dict
        """
        return self.get("about").json()

    def get_logged_in_user(self) -> dict:
        """Returns the currently logged in user, or None if not logged in.
        
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: currently logged in user, or None if not logged in
        :rtype: dict
        """
        return self.get(["auth", "logged_in_user"]).json()

    def get_my_user_id(self) -> str:
        """Returns the ID of the logged in user, or None if not logged in.
        
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: the ID of the logged in user, or None if not logged in
        :rtype: str
        """
        u = self.get_logged_in_user()
        return u["id"] if u and "id" in u else None

    def is_logged_in(self) -> bool:
        """Returns whether the user is currently logged in or not.
        
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: whether the user is currently logged in or not
        :rtype: bool
        """
        return self.session != None and self.get_logged_in_user() != None

    def _check_login(self):
        """Checks whether user is logged in and raises an :py:class:`.exceptions.PineClientAuthException` if not.
        
        :raises exceptions.PineClientAuthException: if not logged in
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        """        
        if not self.is_logged_in():
            raise exceptions.PineClientAuthException("User is not logged in.")

    def get_auth_module(self) -> str:
        """Returns the PINE authentication module, e.g. ``"eve"``.
        
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: the PINE authentication module, e.g. ``"eve"``
        :rtype: str
        """
        return self.get(["auth", "module"]).json()

    def login_eve(self, username: str, password: str) -> bool:
        """Logs in using eve credentials, and returns whether it was successful.
        
        :param username: username
        :type username: str
        :param password: password
        :type password: str
        
        :raises exceptions.PineClientAuthException: if auth module is not eve or login was not successful
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: whether the login was successful
        :rtype: bool
        """
        if self.get_auth_module() != "eve":
            raise exceptions.PineClientAuthException("Auth module is not eve.")
        if self.session:
            self.logout()
        self.session = requests.Session()
        try:
            self.post(["auth", "login"], json={
                "username": username,
                "password": password
            })
            return True
        except exceptions.PineClientHttpException as e:
            self.session.close()
            self.session = None
            if e.resp.status_code == 401:
                raise exceptions.PineClientAuthException("Login failed for {}".format(username), cause=e)
            else:
                raise e

    def logout(self):
        """Logs out the current user.
        
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        """
        if self.is_logged_in():
            self.post(["auth", "logout"])
            if self.session:
                self.session.close()
                self.session = None

    def get_pipelines(self) -> typing.List[dict]:
        """Returns all pipelines accessible to logged in user.
        
        :raises exceptions.PineClientAuthException: if not logged in
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: all pipelines accessible to logged in user
        :rtype: list(dict)
        """
        self._check_login()
        return self.get("pipelines").json()[models.ITEMS_FIELD]

    def collection_builder(self, **kwargs: dict) -> models.CollectionBuilder:
        r"""Makes and returns a new :py:class:`.models.CollectionBuilder` with the logged in user.
        
        :param \**kwargs: any additional args to pass in to the constructor
        :type \**kwargs: dict
        
        :returns: a new :py:class:`.models.CollectionBuilder` with the logged in user
        :rtype: models.CollectionBuilder
        """
        return models.CollectionBuilder(creator_id=self.get_my_user_id(), **kwargs)

    def create_collection(self, builder: models.CollectionBuilder) -> str:
        """Creates a collection using the current value of the given builder and returns its ID.
        
        :param builder: collection builder
        :type builder: models.CollectionBuilder
        
        :raises exceptions.PineClientValueException: if the given collection is not valid, see :py:func:`.models.is_valid_collection`
        :raises exceptions.PineClientAuthException: if not logged in
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: the created collection's ID
        :rtype: str
        """
        self._check_login()
        if builder == None or not isinstance(builder, models.CollectionBuilder):
            raise exceptions.PineClientValueException(builder, "CollectionBuilder")
        if not builder.is_valid(self.logger.warn):
            raise exceptions.PineClientValueException(builder, "collection")
        return self.post("collections", data=builder.form_json, files=builder.files).json()[models.ID_FIELD]

    def get_collection_documents(self, collection_id: str, truncate: bool, truncate_length: int = 30) -> typing.List[dict]:
        """Returns all the documents in the given collection.
        
        :param collection_id: the ID of the collection
        :type collection_id: str
        :param truncate: whether to truncate the document text (a good idea unless you need it)
        :type truncate: bool
        :param truncate_length: how many characters of the text you want if truncated, defaults to ``30``
        :type truncate_length: int, optional
        
        :returns: all the documents in the given collection
        :rtype: list(dict)
        """
        return self.get(["documents", "by_collection_id_all", collection_id], params={
            "truncate": json.dumps(truncate),
            "truncateLength": json.dumps(truncate_length)
        }).json()["_items"]

    def add_document(self, document: dict = {}, creator_id: str = None, collection_id: str = None,
                     overlap: int = None, text: str = None, metadata: dict = None) -> str:
        """Adds a new document to a collection and returns its ID.
        
        Will use the logged in user ID for the creator_id if none is given.  Although all the
        parameters are optional, you must provide values either in the document or through the
        kwargs in order to make a valid document.
        
        :param document: optional document dict, will be overridden with any kwargs, defaults to ``{}``
        :type document: dict, optional
        :param creator_id: optional creator_id for the document, defaults to ``None`` (not set)
        :type creator_id: str, optional
        :param collection_id: optional collection_id for the document, defaults to ``None`` (not set)
        :type collection_id: str, optional
        :param overlap: optional overlap for the document, defaults to ``None`` (not set)
        :type overlap: int, optional
        :param text: optional text for the document, defaults to ``None`` (not set)
        :type text: str, optional
        :param metadata: optional metadata for the document, defaults to ``None`` (not set)
        :type metadata: dict, optional
        
        :raises exceptions.PineClientValueException: if the given document parameters are not valid, see :py:func:`.models.is_valid_eve_document`
        :raises exceptions.PineClientAuthException: if not logged in
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: the created document's ID
        :rtype: str
        """
        self._check_login()
        user_id = self.get_my_user_id()
        if document == None or not isinstance(document, dict):
            document = {}
        if creator_id:
            document["creator_id"] = creator_id
        elif not "creator_id" in document:
            document["creator_id"] = user_id
        if collection_id:
            document["collection_id"] = collection_id
        if overlap != None:
            document["overlap"] = overlap
        if text:
            document["text"] = text
        if metadata != None:
            document["metadata"] = metadata
        if not models.is_valid_eve_document(document, self.logger.warn):
            raise exceptions.PineClientValueException(document, "documents")
        return self.post("documents", json=document).json()[models.ID_FIELD]

    def add_documents(self, documents: typing.List[dict], creator_id: str = None, collection_id: str = None) -> typing.List[str]:
        """Adds multiple documents at once and returns their IDs.
        
        Will use the logged in user ID for the creator_id if none is given.
        
        :param documents: the documents to add
        :type documents: list(dict)
        :param creator_id: optional creator_id to set in the documents, defaults to ``None`` (not set)
        :type creator_id: str, optional
        :param collection_id: optional collection_id to set in the documents, defaults to ``None`` (not set)
        :type collection_id: str, optional
        
        :raises exceptions.PineClientValueException: if any of the given documents are not valid, see :py:func:`.models.is_valid_eve_document`
        :raises exceptions.PineClientAuthException: if not logged in
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: the created documents' IDs
        :rtype: list(str)
        """
        self._check_login()
        user_id = self.get_my_user_id()
        if documents == None or (not isinstance(documents, list) and not isinstance(documents, tuple)):
            raise exceptions.PineClientValueException(documents, "documents")
        for document in documents:
            if creator_id:
                document["creator_id"] = creator_id
            elif "creator_id" not in document or not document["creator_id"]:
                document["creator_id"] = user_id
            if collection_id:
                document["collection_id"] = collection_id
            if not models.is_valid_eve_document(document, self.logger.warn):
                raise exceptions.PineClientValueException(document, "documents")
        return [doc["_id"] for doc in self.post("documents", json=documents).json()[models.ITEMS_FIELD]]

    def annotate_document(self, document_id: str, doc_annotations: typing.List[str], ner_annotations: typing.List[typing.Union[dict, list, tuple]]) -> str:
        """Annotates the given document with the given values.
        
        :param document_id: the document ID to annotate
        :type document_id: str
        :param doc_annotations: document annotations/labels
        :type doc_annotations: list(str)
        :param ner_annotations: NER annotations, where each annotation is either a list or a dict
        :type ner_annotations: list
        
        :raises exceptions.PineClientValueException: if any of the given annotations are not valid, see :py:func:`.models.is_valid_annotation`
        :raises exceptions.PineClientAuthException: if not logged in
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: the annotation ID
        :rtype: str
        """
        self._check_login()
        if not document_id or not isinstance(document_id, str):
            raise exceptions.PineClientValueException(document_id, "str")
        body = {
            "doc": doc_annotations,
            "ner": ner_annotations
        }
        if not models.is_valid_annotation(body, self.logger.warn):
            raise exceptions.PineClientValueException(body, "annotation")

        return self.post(["annotations", "mine", "by_document_id", document_id], json=body).json()

    def annotate_collection_documents(self, collection_id: str, document_annotations: dict, skip_document_updates=False) -> typing.List[str]:
        """Annotates documents in a collection.
        
        :param collection_id: the ID of the collection containing the documents to annotate
        :type collection_id: str
        :param document_annotations: a dict containing "ner" list and "doc" list
        :type document_annotations: dict
        :param skip_document_updates: whether to skip updating the document "has_annotated" map, defaults to ``False``.
                                      This should only be ``True`` if you properly set the
                                      "has_annotated" map when you created the document.
        :type skip_document_updates: bool
        
        :raises exceptions.PineClientValueException: if any of the given annotations are not valid, see :py:func:`.models.is_valid_doc_annotations`
        :raises exceptions.PineClientAuthException: if not logged in
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: the annotation IDs
        :rtype: list(str)
        """
        self._check_login()
        if not models.is_valid_doc_annotations(document_annotations, self.logger.warn):
            raise exceptions.PineClientValueException(document_annotations, "document_annotations")
        return self.post(["annotations", "mine", "by_collection_id", collection_id],
                         json=document_annotations,
                         params={"skip_document_updates":json.dumps(skip_document_updates)}).json()

    def list_collections(self, include_archived: bool = False) -> typing.List[dict]:
        """Returns a list of user's collections.
        
        :param include_archived: whether to include archived collections, defaults to ``False``
        :type include_archived: bool
        
        :raises exceptions.PineClientAuthException: if not logged in
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error
        
        :returns: user's collections
        :rtype: list(dict)
        """
        self._check_login()
        cols = self.get(["collections", "unarchived"]).json()["_items"]
        if include_archived:
            cols += self.get(["collections", "archived"]).json()["_items"]
        for col in cols:
            models.remove_eve_fields(col, remove_timestamps=False)
        return cols

    def download_collection_data(self, collection_id: str, include_collection_metadata: bool = True,
                                 include_document_metadata: bool = True, include_document_text: bool = True,
                                 include_annotations: bool = True, include_annotation_latest_version_only: bool = True):
        """Downloads collection data.
        
        :param collection_id: the ID of the collection for which to download data
        :type collection_id: str
        :param include_collection_metadata: whether to include collection metadata, defaults to ``True``
        :type include_collection_metadata: bool
        :param include_document_metadata: whether to include document metadata, defaults to ``True``
        :type include_document_metadata: bool
        :param include_document_text: whether to include document text, defaults to ``True``
        :type include_document_text: bool
        :param include_annotations: whether to include annotations, defaults to ``True``
        :type include_annotations: bool
        :param include_annotation_latest_version_only: whether to include only the latest version
                        of annotations (``True``) or all versions (``False``), defaults to ``True``
        :type include_annotation_latest_version_only: bool
        
        :raises exceptions.PineClientValueException: if given empty collection ID
        :raises exceptions.PineClientAuthException: if not logged in
        :raises exceptions.PineClientHttpException: if the HTTP request returns an error, such as if the
                                                    collection doesn't exist

        :returns: collection data
        :rtype: dict
        """
        self._check_login()
        if not collection_id:
            raise exceptions.PineClientValueException(collection_id, "str")
        return self.get(["collections", "by_id", collection_id, "download"], params={
            "as_file": json.dumps(False),
            "include_collection_metadata": json.dumps(include_collection_metadata),
            "include_document_metadata": json.dumps(include_document_metadata),
            "include_document_text": json.dumps(include_document_text),
            "include_annotations": json.dumps(include_annotations),
            "include_annotation_latest_version_only": json.dumps(include_annotation_latest_version_only)
        }).json()


class LocalPineClient(PineClient):
    """A client for a local PINE instance, including an :py:class<.EveClient>.
    """

    def __init__(self, backend_base_uri: str, eve_base_uri: str, mongo_base_uri: str = None, mongo_dbname: str = EveClient.DEFAULT_DBNAME):
        """Constructor.
        
        :param backend_base_uri: the base URI for the backend server, e.g. ``"http://localhost:5000"``
        :type backend_base_uri: str
        :param eve_base_uri: the base URI for the eve server, e.g. ``"http://localhost:5001"``
        :type eve_base_uri: str
        :param mongo_base_uri: the base URI for the mongodb server, e.g. ``"mongodb://localhost:27018"``, defaults to ``None``
        :type mongo_base_uri: str, optional
        :param mongo_dbname: the DB name that PINE uses, defaults to ``"pmap_nlp"``
        :type mongo_dbname: str, optional
        """
        
        super().__init__(backend_base_uri)
        self.eve: EveClient = EveClient(eve_base_uri, mongo_base_uri, mongo_dbname=mongo_dbname)
        """The local :py:class:`EveClient` instance.
        
        :type: EveClient
        """

    @overrides
    def is_valid(self) -> bool:
        return super().is_valid() and self.eve.is_valid()
