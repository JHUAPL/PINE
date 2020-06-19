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
