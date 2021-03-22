# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

"""PINE client exceptions module.
"""

import requests

class PineClientException(Exception):
    """Base class for PINE client exceptions.
    """

    def __init__(self, message: str, cause: Exception = None):
        """Constructor.
        
        :param message: the message
        :type message: str
        :param cause: optional cause, defaults to ``None``
        :type cause: Exception, optional
        """
        super().__init__(message)
        if cause:
            self.__cause__ = cause
        self.message = message
        """The message.
        
        :type: str
        """

class PineClientHttpException(PineClientException):
    """A PINE client exception caused by an underlying HTTP exception.
    """

    def __init__(self, method: str, path: str, resp: requests.Response):
        """Constructor.
        
        :param method: the REST method (``"get"``, ``"post"``, etc.)
        :type method: str
        :param path: the human-readable path that caused the exception
        :type path: str
        :param resp: the :py:class:`Response <requests.Response>` with the error info
        :type resp: requests.Response
        """
        super().__init__("HTTP error with {} to {}: {} ({})".format(method, path, resp.status_code, resp.reason))
        self.resp: requests.Response = resp
        """The :py:class:`Response <requests.Response>` with the error info
        
        :type: requests.Response
        """

    @property
    def status_code(self):
        return self.resp.status_code

class PineClientValueException(PineClientException):
    """A PINE client exception caused by passing invalid data.
    """

    def __init__(self, obj: dict, obj_type: str):
        """Constructor.
        
        :param obj: the error data
        :type obj: dict
        :param obj_type: human-readable type of object
        :type obj_type: str
        """
        super().__init__("Object is not a valid type of {}".format(obj_type))

class PineClientAuthException(PineClientException):
    pass
