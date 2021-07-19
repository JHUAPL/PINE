# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import abc
import enum

# see models/login.ts in frontend

class LoginFormFieldType(enum.Enum):
    TEXT = "text"
    PASSWORD = "password"

class LoginFormField(object):

    def __init__(self, name: str, display: str, field_type: LoginFormFieldType):
        self.name = name
        self.display = display
        self.type = field_type

    def to_dict(self):
        return {
            "name": self.name,
            "display": self.display,
            "type": self.type.value
        }

class LoginForm(object):
    
    def __init__(self, fields: list, button_text: str):
        self.fields = fields
        self.button_text = button_text

    def to_dict(self):
        return {
            "fields": [field.to_dict() for field in self.fields],
            "button_text": self.button_text
        }

# see models/user.ts in frontend

class AuthUser(object):

    def __init__(self):
        pass

    @property
    @abc.abstractmethod
    def id(self):
        pass
    
    @property
    @abc.abstractmethod
    def username(self):
        pass
    
    @property
    @abc.abstractmethod
    def display_name(self):
        pass

    @property
    @abc.abstractmethod
    def is_admin(self):
        pass

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name,
            "is_admin": self.is_admin
        }
 
class UserDetails(object):
     
    def __init__(self, first_name, last_name, description):
        self.first_name = first_name
        self.last_name = last_name
        self.description = description
     
    def to_dict(self):
        return self.__dict__

class CollectionUserPermissions(object):
    """Collection permissions for a user as a dictionary of boolean flags.
    """
    # this class should be updated in the following places:
    # * backend/pine/backend/models.py
    # * client/pine/client/models.py
    # * frontend/annotation/src/app/model/collection.ts
    
    def __init__(self, view = False, annotate = False, add_documents = False, add_images = False,
                 modify_users = False, modify_labels = False, modify_document_metadata = False,
                 download_data = False, archive = False, delete_documents = False):
        self.view: bool = view
        """Whether the user can view the collection and documents.
        :type: bool
        """
        self.annotate: bool = annotate
        """Whether the user can annotate collection documents.
        :type: bool
        """
        self.add_documents: bool = add_documents
        """Whether the user can add documents to the collection.
        :type: bool
        """
        self.add_images: bool = add_images
        """Whether the user can add images to the collection.
        :type: bool
        """
        self.modify_users: bool = modify_users
        """Whether the user can modify the list of viewers/annotators for the collection.
        :type: bool
        """
        self.modify_labels: bool = modify_labels
        """Whether the user can modify the list of labels for the collection.
        :type: bool
        """
        self.modify_document_metadata: bool = modify_document_metadata
        """Whether the user can modify document metadata (such as changing the image).
        :type: bool
        """
        self.download_data: bool = download_data
        """Whether the user can download the collection data
        :type: bool
        """
        self.archive: bool = archive
        """Whether the user can archive or unarchive the collection.
        :type: bool
        """
        self.delete_documents: bool = delete_documents
        """Whether the user can delete documents in the collection.
        :type: bool
        """

    def to_dict(self) -> dict:
        """Returns a dict version of this object for conversion to JSON.
        
        :returns: a dict version of this object for conversion to JSON
        :rtype: dict
        """
        return self.__dict__
