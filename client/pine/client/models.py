# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import io
import json
import typing

ID_FIELD: str = "_id"
"""The field used to store database ID.

:type: str
"""

ITEMS_FIELD: str = "_items"
"""The field used to access the items in a multi-item database response.

:type: str
"""

def _check_field_required_bool(obj: dict, field: str) -> bool:
    """Checks that the given field is in the object and is a bool.
    
    :param obj: the object to check
    :type obj: dict
    :param field: the field to check
    :type field: str
    
    :returns: whether the given field is in the object and is a bool
    :rtype: bool
    """
    return field in obj and isinstance(obj[field], bool)

def _check_field_int(obj: dict, field: str) -> bool:
    """Checks that if the given field is in the object, that it is an int.
    
    :param obj: the object to check
    :type obj: dict
    :param field: the field to check
    :type field: str
    
    :returns: if the given field is in the object, that it is an int
    :rtype: bool
    """
    return field not in obj or (obj[field] != None and isinstance(obj[field], int))

def _check_field_required_int(obj: dict, field: str) -> bool:
    """Checks that the given field is in the object and is an int.
    
    :param obj: the object to check
    :type obj: dict
    :param field: the field to check
    :type field: str
    
    :returns: whether the given field is in the object and is an int
    :rtype: bool
    """
    return field in obj and obj[field] != None and isinstance(obj[field], int)

def _check_field_float(obj: dict, field: str) -> bool:
    """Checks that if the given field is in the object, that it is a float.
    
    :param obj: the object to check
    :type obj: dict
    :param field: the field to check
    :type field: str
    
    :returns: if the given field is in the object, that it is a float
    :rtype: bool
    """
    return field not in obj or (object[field] != None and (isinstance(obj[field], float) or isinstance(obj[field], int)))

def _check_field_required_float(obj: dict, field: str) -> bool:
    """Checks that the given field is in the object and is a float.
    
    :param obj: the object to check
    :type obj: dict
    :param field: the field to check
    :type field: str
    
    :returns: whether the given field is in the object and is a float
    :rtype: bool
    """
    return field in obj and obj[field] != None and (isinstance(obj[field], float) or isinstance(obj[field], int))

def _check_field_string(obj: dict, field: str) -> bool:
    """Checks that if the given field is in the object, that it is a string.
    
    :param obj: the object to check
    :type obj: dict
    :param field: the field to check
    :type field: str
    
    :returns: if the given field is in the object, that it is a string
    :rtype: bool
    """
    return field not in obj or isinstance(obj[field], str)

def _check_field_required_string(obj: dict, field: str) -> bool:
    """Checks that the given field is in the object and is a string.
    
    :param obj: the object to check
    :type obj: dict
    :param field: the field to check
    :type field: str
    
    :returns: whether the given field is in the object and is a string
    :rtype: bool
    """
    return field in obj and obj[field] != None and isinstance(obj[field], str) and len(obj[field].strip()) != 0

def _check_field_string_list(obj: dict, field: str, min_length: int = 0) -> bool:
    """Checks that if the given field is in the object, that it is a string list.
    
    :param obj: the object to check
    :type obj: dict
    :param field: the field to check
    :type field: str
    :param min_length: the minimum length of the list (if > 0), defaults to 0
    :type min_length: int, optional
    
    :returns: if the given field is in the object, that it is a string list
    :rtype: bool
    """
    if field not in obj:
        return True
    if not isinstance(obj[field], list) and not isinstance(obj[field], tuple):
        return False
    if min_length > 0 and len(obj[field]) < min_length:
        return False
    for elem in obj[field]:
        if obj == None or not isinstance(elem, str) or len(elem.strip()) == 0:
            return False
    return True

def _check_field_required_string_list(obj: dict, field: str, min_length: int = 0) -> bool:
    """Checks that the given field is in the object and is a string list.
    
    :param obj: the object to check
    :type obj: dict
    :param field: the field to check
    :type field: str
    :param min_length: the minimum length of the list (if > 0), defaults to 0
    :type min_length: int, optional
    
    :returns: if the given field is in the object, that it is a string list
    :rtype: bool
    """
    if field not in obj or obj[field] == None or (not isinstance(obj[field], list) and not isinstance(obj[field], tuple)):
        return False
    if min_length > 0 and len(obj[field]) < min_length:
        return False
    for elem in obj[field]:
        if obj == None or not isinstance(elem, str) or len(elem.strip()) == 0:
            return False
    return True

def _check_field_dict(obj: dict, field: str) -> bool:
    """Checks that if the given field is in the object, that it is a dict.
    
    :param obj: the object to check
    :type obj: dict
    :param field: the field to check
    :type field: str
    
    :returns: if the given field is in the object, that it is a dict
    :rtype: bool
    """
    return field not in obj or isinstance(obj[field], dict)

def _check_field_required_dict(obj: dict, field: str) -> bool:
    """Checks that the given field is in the object and is a dict.
    
    :param obj: the object to check
    :type obj: dict
    :param field: the field to check
    :type field: str
    
    :returns: whether the given field is in the object and is a dict
    :rtype: bool
    """
    return field in obj and obj[field] != None and isinstance(obj[field], dict)

def _check_field_bool(obj: dict, field: str) -> bool:
    """Checks that if the given field is in the object, that it is a bool.
    
    :param obj: the object to check
    :type obj: dict
    :param field: the field to check
    :type field: str
    
    :returns: if the given field is in the object, that it is a bool
    :rtype: bool
    """
    return field not in obj or isinstance(obj[field], bool)

####################################################################################################

def is_valid_eve_user(user: dict, error_callback: typing.Callable[[str], None] = None) -> bool:
    """Checks whether the given user object is valid.
    
    A valid user object has an ``_id``, ``firstname``, and ``lastname`` that are non-empty string
    fields.  If ``email``, ``description``, or ``passwdhash`` are present, they are string fields.
    If ``role`` is present, it is a list of strings that are either ``administrator`` or ``user``.
    
    :param user: user object
    :type user: dict
    :param error_callback: optional callback that is called with any error messages, defaults to ``None``
    :type error_callback: function, optional
    
    :returns: whether the given user object is valid
    :rtype: bool
    """
    if user == None or not isinstance(user, dict):
        if error_callback:
            error_callback("Given object is not a dict.")
        return False
    if not _check_field_required_string(user, ID_FIELD) or \
       not _check_field_required_string(user, "firstname") or \
       not _check_field_required_string(user, "lastname"):
        if error_callback:
            error_callback("Given object is missing {}, firstname, or lastname fields.".format(ID_FIELD))
        return False
    if not _check_field_string(user, "email") or \
       not _check_field_string(user, "description") or \
       not _check_field_string(user, "passwdhash"):
        if error_callback:
            error_callback("Fields email, description, or passwd hash are not valid.")
        return False
    if "role" in user:
        if user["role"] == None or (not isinstance(user["role"], list) and not isinstance(user["role"], tuple)):
            if error_callback:
                error_callback("Field role is not a list.")
            return False
        for role in user["role"]:
            if role == None or not isinstance(role, str) or role not in ["administrator", "user"]:
                error_callback("One or mole roles is not valid.")
                return False

    return True

def is_valid_eve_pipeline(pipeline: dict, error_callback: typing.Callable[[str], None] = None) -> bool:
    """Checks whether the given pipeline object is valid.
    
    A valid pipeline has an ``_id``, ``title``, and ``name`` that are non-empty string fields.  If
    ``description`` is provided, it is a string field.  If ``parameters`` are provided, it is a
    dict field.
    
    :param pipeline: pipeline object
    :type pipeline: dict
    :param error_callback: optional callback that is called with any error messages, defaults to ``None``
    :type error_callback: function, optional
    
    :returns: whether the given pipeline object is valid
    :rtype: bool
    """
    if pipeline == None or not isinstance(pipeline, dict):
        if error_callback:
            error_callback("Given object is not a dict.")
        return False
    if not _check_field_required_string(pipeline, ID_FIELD) or \
       not _check_field_required_string(pipeline, "title") or \
       not _check_field_required_string(pipeline, "name"):
        if error_callback:
            error_callback("Given object is missing {}, title, or name fields.".format(ID_FIELD))
        return False
    if not _check_field_string(pipeline, "description"):
        if error_callback:
            error_callback("Field description is not valid.")
        return False
    if "parameters" in pipeline and (pipeline["parameters"] == None or not isinstance(pipeline["parameters"], dict)):
        if error_callback:
            error_callback("Field parameters is not a dict.")
        return False
                
    return True

def is_valid_eve_collection(collection: dict, error_callback: typing.Callable[[str], None] = None) -> bool:
    """Checks whether the given collection object is valid.
    
    A valid collection has a ``creator_id`` that is a non-empty string field.  It has a ``labels``
    that is a non-empty list of strings.  If ``annotators`` or ``viewers`` are provided, they are
    lists of strings.  If ``metadata`` or ``configuration`` are provided, they are dicts.  If
    ``archived`` is provided, it is a bool.
    
    :param collection: collection object
    :type collection: dict
    :param error_callback: optional callback that is called with any error messages, defaults to ``None``
    :type error_callback: function, optional
    
    :returns: whether the given collection object is valid
    :rtype: bool
    """
    if collection == None or not isinstance(collection, dict):
        if error_callback:
            error_callback("Given object is not a dict.")
        return False
    if not _check_field_required_string(collection, "creator_id") or \
       not _check_field_required_string_list(collection, "labels"):
        if error_callback:
            error_callback("Given object is missing creator_id or labels fields.")
        return False
    if not _check_field_string_list(collection, "annotators") or \
       not _check_field_string_list(collection, "viewers") or \
       not _check_field_dict(collection, "metadata") or \
       not _check_field_dict(collection, "configuration") or \
       not _check_field_bool(collection, "archived"):
        if error_callback:
            error_callback("Field annotators, viewers, metadata, configuration, or archived is not valid.")
        return False
    
    return True

def is_valid_collection(form: dict, files: dict, error_callback: typing.Callable[[str], None] = None) -> bool:
    """Checks whether the given form and files parameters are valid for creating a collection.
    
    A valid form has a ``collection`` that is a dict field and is valid via
    :py:func:`.is_valid_eve_collection`.  Additionally, the collection has string ``title`` and
    ``description`` fields in its ``metadata``.  It also has at least one element for ``labels``,
    ``viewers``, and ``annotators``, and the ``creator_id`` must be in both ``viewers`` and
    ``annotators``.
    
    The form also has ``overlap`` as a float field between 0 and 1 (inclusive), ``train_every`` as
    an int field that is at least 5, and ``pipelineId`` as a string field.
    
    If files are provided, file ``file`` and any files starting with ``imageFile`` are checked.
    If a file ``file`` is provided, the form must also have a boolean ``csvHasHeader`` field and an
    int ``csvTextCol`` field.
    
    :param form: form data to send to backend
    :type form: dict
    :param files: file data to send to backend
    :type files: dict
    :param error_callback: optional callback that is called with any error messages, defaults to ``None``
    :type error_callback: function, optional
    
    :returns: whether the given form and files parameters are valid for creating a collection
    :rtype: bool
    """
    if not form or not isinstance(form, dict) or not _check_field_required_dict(form, "collection"):
        if error_callback:
            error_callback("Missing or invalid collection.")
        return False
    collection = form["collection"]
    if not is_valid_eve_collection(collection, error_callback=error_callback):
        return False
    if not _check_field_required_dict(collection, "metadata"):
        if error_callback:
            error_callback("Missing or invalid metadata.")
        return False
    md = collection["metadata"]
    if not _check_field_required_string(md, "title") or \
       not _check_field_required_string(md, "description"):
        if error_callback:
            error_callback("Missing metadata title or description.")
        return False
    if not _check_field_required_string_list(collection, "labels", 1) or \
       not _check_field_required_string_list(collection, "viewers", 1) or \
       not _check_field_required_string_list(collection, "annotators", 1):
        if error_callback:
            error_callback("Need at least one label, viewer, and annotator.")
        return False
    if collection["creator_id"] not in collection["viewers"] or collection["creator_id"] not in collection["annotators"]:
        if error_callback:
            error_callback("Creator ID should be in viewers and annotators.")
        return False

    if not _check_field_required_float(form, "overlap") or \
       not _check_field_required_int(form, "train_every") or \
       not _check_field_required_string(form, "pipelineId"):
        if error_callback:
            error_callback("Missing fields overlap, train_every, or pipelineId.")
        return False
    if form["overlap"] < 0 or form["overlap"] > 1:
        if error_callback:
            error_callback("Field overlap must be between 0 and 1.")
        return False
    if form["train_every"] < 5:
        if error_callback:
            error_callback("Field train_every must be >= 5.")
        return False

    if files:
        for key in files:
            if key == "file":
                if not _check_field_required_bool(form, "csvHasHeader") or \
                  not _check_field_required_int(form, "csvTextCol"):
                    if error_callback:
                        error_callback("Missing fields csvHasHeader or csvTextCol.")
                    return False
                if not isinstance(files[key], io.IOBase):
                    if error_callback:
                        error_callback("File {} is not an open file.".format(key))
                    return False
            elif key.startswith("imageFile"):
                if not isinstance(files[key], io.IOBase):
                    if error_callback:
                        error_callback("File {} is not an open file.".format(key))
                    return False

    return True

def is_valid_eve_document(document: dict, error_callback: typing.Callable[[str], None] = None) -> bool:
    """Checks whether the given document object is valid.
    
    A valid document has a ``creator_id`` and ``collection_id`` that are non-empty string fields.
    Optionally, it may have an int ``overlap`` field, string ``text``field, and dict
    ``metadata`` and ``has_annotated`` fields.
    
    :param document: document object
    :type document: dict
    :param error_callback: optional callback that is called with any error messages, defaults to ``None``
    :type error_callback: function, optional
    
    :returns: whether the given document object is valid
    :rtype: bool
    """
    if document == None or not isinstance(document, dict):
        if error_callback:
            error_callback("Given object is not a dict.")
        return False
    
    if not _check_field_required_string(document, "creator_id") or \
       not _check_field_required_string(document, "collection_id"):
        if error_callback:
            error_callback("Missing required string fields creator_id and collection_id.")
        return False

    if not _check_field_int(document, "overlap") or \
       not _check_field_string(document, "text") or \
       not _check_field_dict(document, "metadata") or \
       not _check_field_dict(document, "has_annotated"):
        if error_callback:
            error_callback("Invalid fields overlap, text, metadata, or has_annotated.")
        return False

    return True

def is_valid_doc_annotation(ann: typing.Any, error_callback: typing.Callable[[str], None] = None) -> bool:
    """Checks whether the given annotation is a valid document label/annotation.
    
    This means that it is a non-empty string.
    
    :param ann: annotation
    :param error_callback: optional callback that is called with any error messages, defaults to ``None``
    :type error_callback: function, optional
    
    :returns: whether the given annotation is a valid document label/annotation
    :rtype: bool
    """
    if not ann or not isinstance(ann, str):
        if error_callback:
            error_callback("Doc annotation is not a string.")
        return False
    if len(ann.strip()) == 0:
        if error_callback:
            error_callback("Doc annotation is empty.")
        return False
    return True

def is_valid_ner_annotation(ann: typing.Any, error_callback: typing.Callable[[str], None] = None) -> bool:
    """Checks whether the given annotation is a valid document NER annotation.
    
    Valid NER annotations take one of two forms: a :py:class:`dict` or a
    :py:class:`list`/:py:class:`tuple` of size 3.
    
    A valid NER :py:class:`dict` has the following fields:
    
    * ``start``: an :py:class:`int` that is >= 0
    * ``end``: an :py:class:`int` that is >= 0
    * ``label``: a non-empty :py:class:`str`
    
    A valid NER :py:class:`list`/:py:class:`tuple` has the following elements:
    
    * element ``0``: an :py:class:`int` that is >= 0
    * element ``1``: an :py:class:`int` that is >= 0
    * element ``2``: a non-empty :py:class:`str`
    
    :param ann: annotation
    :param error_callback: optional callback that is called with any error messages, defaults to ``None``
    :type error_callback: function, optional
    
    :returns: whether the given annotation is a valid document label/annotation
    :rtype: bool
    """
    if isinstance(ann, dict):
        if not "start" in ann or not ann["start"] or not isinstance(ann["start"], int) or ann["start"] < 0:
            if error_callback:
                error_callback("Field start is not valid ({}).".format(ann["start"] if "start" in ann else None))
            return False
        if not "end" in ann or not ann["end"] or not isinstance(ann["end"], int) or ann["end"] < 0:
            if error_callback:
                error_callback("Field end is not valid ({}).".format(ann["end"] if "end" in ann else None))
            return False
        if not "label" in ann or not ann["label"] or not isinstance(ann["label"], str) or len(ann["label"].strip()) == 0:
            if error_callback:
                error_callback("Field label is not valid ({}).".format(ann["label"] if "label" in ann else None))
            return False
    elif isinstance(ann, list) or isinstance(ann, tuple):
        if len(ann) != 3:
            if error_callback:
                error_callback("Annotation length is not 3.")
            return False
        if not isinstance(ann[0], int) or ann[0] < 0 or not isinstance(ann[1], int) or ann[1] < 0 or \
           not isinstance(ann[2], str) or len(ann[2].strip()) == 0:
            if error_callback:
                error_callback("Annotation's first element must be int, second element must be int, third element must be string.")
            return False
    else:
        if error_callback:
            error_callback("Doc annotation is not a dict  or list({}).".format(type(ann)))
        return False

    return True

def is_valid_annotation(body: dict, error_callback: typing.Callable[[str], None] = None) -> bool:
    """Checks whether the given body is valid to create an annotation.
    
    A valid body is a :py:class:`dict` with two fields:
    
    * ``doc``: a list of valid doc annotations (see :py:func:`.is_valid_doc_annotation`)
    * ``ner``: a list of valid NER annotations (see :py:func:`.is_valid_ner_annotation`)
    
    :param body: annotation body
    :type body: dict
    :param error_callback: optional callback that is called with any error messages, defaults to ``None``
    :type error_callback: function, optional
    
    :returns: whether the given body is valid to create an annotation
    :rtype: bool
    """
    if not body or not isinstance(body, dict):
        if error_callback:
            error_callback("Body is not a dict ({}).".format(type(body)))
        return False

    if not _check_field_required_string_list(body, "doc"):
        if error_callback:
            error_callback("Missing string list field doc.")
        return False
    for ann in body["doc"]:
        if not is_valid_doc_annotation(ann, error_callback=error_callback):
            return False
    if "ner" not in body or (not isinstance(body["ner"], list) and not isinstance(body["ner"], tuple)):
        if error_callback:
            error_callback("Invalid NER annotation field ner.")
        return False
    for ann in body["ner"]:
        if not is_valid_ner_annotation(ann, error_callback=error_callback):
            return False

    return True

def is_valid_doc_annotations(doc_annotations: dict, error_callback: typing.Callable[[str], None] = None) -> bool:
    """Checks whether the given document annotations are valid.
    
    A valid document annotations object is a :py:class:`dict`, where the keys are :py:class:`str`
    document IDs, and the values are valid annotation bodies (see :py:func:`.is_valid_annotation`).
    
    :param doc_annotations: document annotations
    :type body: dict
    :param error_callback: optional callback that is called with any error messages, defaults to ``None``
    :type error_callback: function, optional
    
    :returns: whether the given body is valid to create an annotation
    :rtype: bool
    """
    if not doc_annotations or not isinstance(doc_annotations, dict):
        if error_callback:
            error_callback("Annotations is not a dict ({}).".format(type(doc_annotations)))
        return False
    for doc_id in doc_annotations:
        if not doc_id or not isinstance(doc_id, str) or len(doc_id.strip()) == 0:
            if error_callback:
                error_callback("Document ID is not valid ({}).".format(doc_id))
            return False
        annotations = doc_annotations[doc_id]
        if not is_valid_annotation(annotations, error_callback=error_callback):
            return False

    return True

####################################################################################################

class CollectionBuilder(object):
    """A class that can build the form and files fields that are necessary to create a collection.
    """

    def __init__(self,
                 collection: dict = None,
                 creator_id: str = None,
                 viewers: typing.List[str] = None,
                 annotators: typing.List[str] = None,
                 labels: typing.List[str] = None,
                 title: str = None,
                 description: str = None,
                 allow_overlapping_ner_annotations: bool = None,
                 pipelineId: str = None,
                 overlap: float = None,
                 train_every: int = None,
                 classifierParameters: dict = None,
                 document_csv_file: str = None,
                 document_csv_file_has_header: bool = None,
                 document_csv_file_text_column: int = None,
                 image_files: typing.List[str] = None):
        """Constructor.
        
        :param collection: starting parameters for the collection, defaults to ``None`` (not set)
        :type collection: dict, optional
        :param creator_id: user ID for the creator, see :py:meth:`.creator_id`, defaults to ``None`` (not set)
        :type creator_id: str, optional
        :param viewers: viewer IDs for the collection, see :py:meth:`.viewer`, defaults to ``None`` (not set)
        :type viewers: list(str), optional
        :param annotators: annotator IDs for the collection, see :py:meth:`.annotator`, defaults to ``None`` (not set)
        :type annotators: list(str), optional
        :param labels: labels for the collection, see :py:meth:`.label`, defaults to ``None`` (not set)
        :type labels: list(str), optional
        :param title: metadata title, see :py:meth:`.title`, defaults to ``None`` (not set)
        :type title: str, optional
        :param description: metadata description, see :py:meth:`.description`, defaults to ``None`` (not set)
        :type description: str, optional
        :param allow_overlapping_ner_annotations: optional configuration for allowing overlapping NER
                                                  annotations, see :py:meth:`.allow_overlapping_ner_annotations`,
                                                  defaults to ``None`` (not set)
        :type allow_overlapping_ner_annotations: bool
        :param pipelineId: the ID of the pipeline from which to create the classifier,
                           see :py:meth:`.classifier`, defaults to ``None`` (not set)
        :type pipelineId: str, optional
        :param overlap: the classifier overlap, see :py:meth:`.classifier`, defaults to ``None`` (not set)
        :type overlap: float, optional
        :param train_every: train the model after this many documents are annotated,
                            see :py:meth:`.classifier`, defaults to ``None`` (not set)
        :type train_every: int, optional
        :param classifierParameters: any parameters to pass to the classifier,
                                     see :py:meth:`.classifier`, defaults to ``None`` (not set)
        :type classifierParameters: dict, optional
        :param document_csv_file: the filename of the local document CSV file,
                                  see :py:meth:`.document_csv_File`, defaults to ``None`` (not set)
        :type document_csv_file: str, optional
        :param document_csv_file_has_header: whether the document CSV file has a header,
                                             see :py:meth:`.document_csv_File`, defaults to ``None`` (not set)
        :type document_csv_file_has_header: bool, optional
        :param document_csv_file_text_column: if the document CSV file has headers, the document text
                                              can be found in this column index (the others are used for
                                              document metadata), see :py:meth:`.document_csv_File`,
                                              defaults to ``None`` (not set)
        :type document_csv_file_text_column: int, optional
        :param image_files: any image files to add to the collection, see :py:meth:`.image_file`,
                            defaults to ``None`` (not set)
        :type image_files: list(str)
        """

        self.form = {
            "collection": {
                "creator_id": None,
                "metadata": {
                    "title": None,
                    "description": None
                },
                "configuration": {
                },
                "labels": None,
                "viewers": None,
                "annotators": None
            }
        }
        """The form data.
        
        :type: dict
        """
        if collection:
            self.form["collection"].update(collection)
        self.files = {}
        """The files data.
        
        :type: dict
        """
        self._image_file_counter = 0
        if creator_id:
            self.creator_id(creator_id)
        if viewers:
            for viewer in viewers: self.viewer(viewer)
        if annotators:
            for annotator in annotator: self.annotator(annotator)
        if labels:
            for label in labels: self.label(label)
        if title:
            self.title(title)
        if description:
            self.description(description)
        if allow_overlapping_ner_annotations != None:
            self.allow_overlapping_ner_annotations(allow_overlapping_ner_annotations)
        if document_csv_file and document_csv_file_has_header != None and document_csv_file_text_column != None:
            self.document_csv_file(document_csv_file, document_csv_file_has_header, document_csv_file_text_column)
        if image_files:
            for image_file in image_files: self.image_file(image_file)
        if pipelineId:
            kwargs = {}
            if overlap != None: kwargs["overlap"] = overlap
            if train_every != None: kwargs["train_every"] = train_every
            if classifierParameters != None: kwargs["classifierParameters"] = classifierParameters
            self.classifier(pipelineId, **kwargs)

    @property
    def collection(self) -> dict:
        """Returns the collection information from the form.
        
        :returns: collection information from the form
        :rtype: dict
        """
        return self.form["collection"]

    @property
    def form_json(self) -> dict:
        """Returns the form where the values have been JSON-encoded.
        
        :returns: the form where the values have been JSON-encoded
        :rtype: dict
        """
        return {key: json.dumps(value) for (key, value) in self.form.items()}

    def creator_id(self, user_id: str) -> "CollectionBuilder":
        """Sets the creator_id to the given, and adds to viewers and annotators.
        
        :param user_id: the user ID to use for the creator_id
        :type user_id: str
        
        :returns: self
        :rtype: models.CollectionBuilder
        """
        self.collection["creator_id"] = user_id
        self.viewer(user_id)
        self.annotator(user_id)
        return self

    def viewer(self, user_id: str) -> "CollectionBuilder":
        """Adds the given user to the list of viewers.
        
        :param user_id: the user ID to add as a viewer
        :type user_id: str
        
        :returns: self
        :rtype: models.CollectionBuilder
        """
        if not self.collection["viewers"]:
            self.collection["viewers"] = [user_id]
        elif user_id not in self.collection["viewers"]:
            self.collection["viewers"].append(user_id)
        return self

    def annotator(self, user_id: str) -> "CollectionBuilder":
        """Adds the given user to the list of annotators.
        
        :param user_id: the user ID to add as an annotator
        :type user_id: str
        
        :returns: self
        :rtype: models.CollectionBuilder
        """
        if not self.collection["annotators"]:
            self.collection["annotators"] = [user_id]
        elif user_id not in self.collection["annotators"]:
            self.collection["annotators"].append(user_id)
        return self

    def label(self, label: str) -> "CollectionBuilder":
        """Adds the given label to the collection.
        
        :param label: label to add
        :type label: str
        
        :returns: self
        :rtype: models.CollectionBuilder
        """
        if not self.collection["labels"]:
            self.collection["labels"] = [label]
        elif label not in self.collection["labels"]:
            self.collection["labels"].append(label)
        return self

    def metadata(self, key: str, value: typing.Any) -> "CollectionBuilder":
        """Adds the given metadata key/value to the collection.
        
        :param key: metadata key
        :type key: str
        :param value: metadata value
        
        :returns: self
        :rtype: models.CollectionBuilder
        """
        self.collection["metadata"][key] = value
        return self

    def title(self, title: str) -> "CollectionBuilder":
        """Sets the metadata title to the given.
        
        :param title: collection title
        :type title: str
        
        :returns: self
        :rtype: models.CollectionBuilder
        """
        return self.metadata("title", title)

    def description(self, description: str) -> "CollectionBuilder":
        """Sets the metadata description to the given.
        
        :param description: collection description
        :type description: str
        
        :returns: self
        :rtype: models.CollectionBuilder
        """
        return self.metadata("description", description)

    def configuration(self, key: str, value: typing.Any) -> "CollectionBuilder":
        """Adds the given configuration key/value to the collection.
        
        :param key: configuration key
        :type key: str
        :param value: configuration value
        
        :returns: self
        :rtype: models.CollectionBuilder
        """
        self.collection["configuration"][key] = value
        return self

    def allow_overlapping_ner_annotations(self, allow_overlapping_ner_annotations: bool):
        """Sets the configuration value for allow_overlapping_ner_annotations to the given.
        
        :param allow_overlapping_ner_annotations: whether to allow overlapping NER annotations
        :type allow_overlapping_ner_annotations: bool
        
        :returns: self
        :rtype: models.CollectionBuilder
        """
        return self.configuration("allow_overlapping_ner_annotations", allow_overlapping_ner_annotations)

    def classifier(self, pipelineId: str, overlap: float = 0, train_every: int = 100, classifierParameters: dict = {}) -> "CollectionBuilder":
        """Sets classifier information for the created collection.
        
        :param pipelineId: the ID of the pipeline from which to create the classifier
        :type pipelineId: str
        :param overlap: the classifier overlap, defaults to `0`
        :type overlap: float, optional
        :param train_every: train the model after this many documents are annotated, defaults to `100`
        :type train_every: int, optional
        :param classifierParameters: any parameters to pass to the classifier, defaults to ``{}``
        :type classifierParameters: dict, optional
        
        :returns: self
        :rtype: models.CollectionBuilder
        """
        self.form["pipelineId"] = pipelineId
        self.form["overlap"] = overlap
        self.form["train_every"] = train_every
        self.form["classifierParameters"] = classifierParameters
        return self

    def document_csv_file(self, csv_filename: str, has_header: bool, text_column: int) -> "CollectionBuilder":
        """Sets the CSV file used to create documents to the given.
        
        May raise an Exception if there is a problem opening the indicated file.
        
        :param csv_filename: the filename of the local CSV file
        :type csv_filename: str
        :param has_header: whether the CSV file has a header
        :type has_header: bool
        :param text_column: if the CSV file has headers, the document text can be found in this column index
                            (the others are used for document metadata)
        :type text_column: int
        
        :returns: self
        :rtype: models.CollectionBuilder
        """
        if "file" in self.files and self.files["file"]:
            self.files["file"].close()
        self.files["file"] = open(csv_filename, "rb")
        self.form["csvHasHeader"] = has_header
        self.form["csvTextCol"] = text_column
        return self

    def image_file(self, image_filename: str) -> "CollectionBuilder":
        """Adds the given image file to the collection.
        
        May raise an Exception if there is a problem opening the indicated file.
        
        :param image_filename: the filename of the local image file
        :type image_filename: str
        
        :returns: self
        :rtype: models.CollectionBuilder
        """
        self.files["imageFile{}".format(self._image_file_counter)] = open(image_filename, "rb")
        self._image_file_counter += 1
        return self

    def is_valid(self, error_callback: typing.Callable[[str], None] = None):
        """Checks whether the currently set values are valid or not.
        
        See :py:func:`.is_valid_collection`.
        
        :param error_callback: optional callback that is called with any error messages, defaults to ``None``
        :type error_callback: function, optional
        
        :returns: whether the currently set values are valid or not
        :rtype: bool
        """
        return is_valid_collection(self.form, self.files, error_callback=error_callback)

####################################################################################################

def remove_eve_fields(obj: dict, remove_timestamps: bool = True, remove_versions: bool = True):
    """Removes fields inserted by eve from the given object.
    
    :param obj: the object
    :type obj: dict
    :param remove_timestamps: whether to remove the timestamp fields, defaults to ``True``
    :type remove_timestamps: bool
    :param remove_versions: whether to remove the version fields, defaults to ``True``
    :type remove_versions: bool
    """
    fields = ["_etag", "_links"]
    if remove_timestamps: fields += ["_created", "_updated"]
    if remove_versions: fields += ["_version", "_latest_version"]
    for f in fields:
        if f in obj:
            del obj[f]

def remove_nonupdatable_fields(obj: dict):
    """Removes all non-updatable fields from the given object.
    
    These fields would cause a ``PUT``/``PATCH`` to be rejected because they are not user-modifiable.
    
    :param obj: the object
    :type obj: dict
    """
    remove_eve_fields(obj)
