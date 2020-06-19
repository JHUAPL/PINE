# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

from eve.io.mongo import Validator
from eve.io.base import BaseJSONEncoder
from bson import ObjectId

class JHED(object):
    def __init__(self, jhed):
        self.jhed = jhed.lower()

    def __str__(self):
        return self.jhed

    def __hash__(self):
        return hash(self.jhed)

    def __eq__(self, other):
        if isinstance(other, JHED):
            return self.jhed == other.jhed
        return NotImplemented


class JHEDValidator(Validator):
    """
    Extends the base mongo validator adding support for the uuid data-type
    """
    def _validate_type_jhed(self, value):
        try:
            JHED(value)
        except ValueError:
            pass
        return True

class JHEDEncoder(BaseJSONEncoder):
    """ JSONEconder subclass used by the json render function.
    This is different from BaseJSONEoncoder since it also addresses
    encoding of UUID
    """

    def default(self, obj):
        if isinstance(obj, JHED):
            return str(obj)
        elif isinstance(obj, ObjectId):
            return str(obj)
        else:
            # delegate rendering to base class method (the base class
            # will properly render ObjectIds, datetimes, etc.)
            return super(JHEDEncoder, self).default(obj)