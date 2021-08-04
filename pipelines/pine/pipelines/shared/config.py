#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# **********************************************************************
# Copyright (C) 2018 Johns Hopkins University Applied Physics Laboratory
#
# All Rights Reserved.
# This material may only be used, modified, or reproduced by or for the
# U.S. government pursuant to the license rights granted under FAR
# clause 52.227-14 or DFARS clauses 252.227-7013/7014.
# For any other permission, please contact the Legal Office at JHU/APL.
# **********************************************************************
import inspect
import json
import logging
import os
import pathlib
from argparse import ArgumentParser
from datetime import timedelta
from importlib.util import find_spec

import six


LOGGER = logging.getLogger(__name__)

class BaseConfig(object):
    # # # # GLOBAL PARAMETERS - ONLY EXTEND - # # # #

    # allow the data root directory to be overwritten by the environment
    ROOT_DIR = os.environ.get("AL_ROOT_DIR",
                              os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir)))
    BASE_DIR = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir))
    BASE_CFG_FILE = "config.yaml"
    BASE_ENV_PREFIX = "AL_"

    # # # # GLOBAL PARAMETERS - ONLY EXTEND - # # # #

    # # # ENVIRONMENT PARAMS # # #
    DEBUG = True
    TESTING = False
    LOGGER_NAME = BASE_ENV_PREFIX + "LOGGER"
    LOGGER_DIR = "logs"
    LOGGER_FILE = "debug.log"
    LOGGER_LEVEL = logging.DEBUG
    PIPELINE = "opennlp"

    # EVE
    EVE_HOST = "localhost"
    EVE_PORT = 5001

    # Redis
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_USR = None
    REDIS_PWD = None
    REDIS_DBNUM = 0  # Redis DB Number (0-5)
    REDIS_PREFIX = "AL:"  # Note: Must be used manually
    REDIS_EXPIRE = 3600
    REDIS_MAX_PROCESSES = 10

    # Scheduler
    SCHEDULER_REGISTRATION_TIMEOUT = int(timedelta(minutes=10).total_seconds())  # how long something will be registered as a service
    SCHEDULER_HANDLER_TIMEOUT = int(timedelta(minutes=10).total_seconds())  # how long it should take to process a service response
    SCHEDULER_QUEUE_TIMEOUT = int(timedelta(minutes=60).total_seconds())  # how long a job can sit in the queue before it expires (e.g. client did not consume)

    # New Services
    SERVICE_REGISTRATION_CHANNEL = "registration"
    SERVICE_REGISTRATION_FREQUENCY = 60  # unit: seconds
    SERVICE_LISTENING_FREQUENCY = 1  # unit: seconds
    SERVICE_HANDLER_TIMEOUT = 60  # unit: seconds
    SERVICE_LIST = [
        dict(
            name="corenlp",
            version="1.0",
            channel="service_corenlp",
            service=dict(
                framework="corenlp",
                types=["fit", "predict", "status"]
            )
        ),
        dict(
            name="opennlp",
            version="1.0",
            channel="service_opennlp",
            service=dict(
                framework="opennlp",
                types=["fit", "predict", "status"]
            )
        ),
        dict(
            name="spacy",
            version="1.0",
            channel="service_spacy",
            service=dict(
                framework="spacy",
                types=["fit", "predict", "status"]
            )
        )
    ]


    # Models
    MODELS_DIR = ROOT_DIR + r"/models"

    def __init__(self, root_dir=None):

        # Default are already loaded at this Point
        if root_dir is not None:
            self._process_paths(root_dir)

        # Read in environment vars
        self._process_file_cfg()  # Load Config File First
        self._process_env_vars()  # Process Env Vars Last

        if getattr(self, "TESTING", False) is True:
            LOGGER.info("Environment<" + self.__class__.__name__ + ">: " + self.as_dict().__str__())

    @classmethod
    def _get_config_var_paths(cls, root_dict=None):

        return_dict = dict()
        root_obj = root_dict if root_dict is not None else cls.as_dict()

        def traverse_dict(dict_obj, _path=None):
            if _path is None:
                _path = []
            for _key, _val in six.iteritems(dict_obj):
                next_path = _path + [_key]
                if isinstance(_val, dict):
                    for _dict in traverse_dict(_val, next_path):
                        yield _dict
                else:
                    yield next_path, _val

        for path, val in traverse_dict(root_obj):
            return_dict[".".join(path)] = val
        return return_dict

    @classmethod
    def _process_paths(cls, alt_path=None):
        norm_alt_path = os.path.normpath(os.path.abspath(alt_path))
        old_root_path = cls.ROOT_DIR
        if not os.path.exists(alt_path):
            return
        white_list = frozenset({"ROOT_DIR", "BASE_DIR"})
        for key, value in six.iteritems(cls.as_dict()):
            if not isinstance(value, str):
                continue
            if key in white_list:
                continue
            if value.startswith(old_root_path) and hasattr(cls, key):
                fixed_path = value.replace(old_root_path, norm_alt_path)
                setattr(cls, key, fixed_path)
                continue
        setattr(cls, "ROOT_DIR", norm_alt_path)
        setattr(cls, "BASE_DIR", norm_alt_path)

    @classmethod
    def _process_file_cfg(cls):
        try:
            from ruamel.yaml import YAML
        except ImportError:
            LOGGER.debug("YAML Parsing not Available")
            return
        yaml = YAML(typ="unsafe", pure=True)
        yaml_path = os.path.join(cls.BASE_DIR, cls.BASE_CFG_FILE)
        yaml_pathlib = pathlib.Path(yaml_path)
        if not (yaml_pathlib.exists() or yaml_pathlib.is_file()):
            LOGGER.debug("YAML Config File not Available")
            return
        config_dict = yaml.load(yaml_pathlib)  # type: dict
        config_dict = config_dict if isinstance(config_dict, dict) else dict()
        config_dict_cls = cls.as_dict()
        white_list = ("ROOT_DIR", "BASE_DIR", "BASE_CFG_FILE")
        if find_spec("pydash"):
            import pydash
            for path, value in six.iteritems(config_dict):
                upper_key = str.upper(path)
                if upper_key not in white_list and pydash.has(config_dict_cls, upper_key):
                    setattr(cls, upper_key, value)
        else:
            for key, value in six.iteritems(config_dict):
                upper_key = str.upper(key)
                if upper_key in config_dict_cls and upper_key not in white_list:
                    setattr(cls, upper_key, value)
        LOGGER.info("YAML Config %s was Loaded" % yaml_path)

    @classmethod
    def _process_env_vars(cls):
        for key, value in six.iteritems(cls.as_dict()):
            is_bool = isinstance(value, bool)
            is_int = isinstance(value, six.integer_types)
            is_flt = isinstance(value, float)
            is_arr = isinstance(value, list)
            is_dict = isinstance(value, dict)
            is_str = isinstance(value, str)
            if hasattr(cls, key):
                # Prefix with DH to avoid potential conflicts
                # Default is the value in the config if not found
                environment_var = os.getenv(cls.BASE_ENV_PREFIX + key, value)
                # default was used
                if environment_var == value:
                    continue
                # special case
                # TODO: Special cases aren't special enough to break the rules
                if environment_var == "null":
                    environment_var = None
                    setattr(cls, key, environment_var)
                    continue

                # first on purpose
                if is_bool:
                    environment_var = cls._str2bool(environment_var, value)
                elif is_int:
                    environment_var = cls._try_cast(environment_var, int, value)
                elif is_flt:
                    environment_var = cls._try_cast(environment_var, float, value)
                elif is_arr or is_dict:
                    try:
                        temp = json.loads(environment_var)
                    except json.decoder.JSONDecodeError as e:
                        LOGGER.error("Invalid Format: " + key, e)
                        continue
                    if is_arr and isinstance(temp, list):
                        environment_var = temp
                    elif is_dict and isinstance(temp, dict):
                        environment_var = temp
                    else:
                        LOGGER.error("Invalid Format: " + key)
                        continue
                # last on purpose
                elif not is_str and value is not None:
                    LOGGER.error("Environment variable %s not supported" % key, environment_var)
                    continue
                setattr(cls, key, environment_var)

    @classmethod
    def as_dict(cls):
        """
        :rtype: dict
        """
        # Doing this because of inheritance chain
        member_list = inspect.getmembers(cls, lambda x: not (inspect.isroutine(x)))
        attribute_list = [mem for mem in member_list if not (mem[0].startswith("__") and mem[0].endswith("__"))]
        return dict(attribute_list)

    @classmethod
    def as_attr_dict(cls):
        """
        :rtype: munch.Munch | dict
        """
        try:
            import munch
            return munch.munchify(cls.as_dict())
        except ImportError:
            LOGGER.error("Attribute Dict not Available")
            return cls.as_dict()

    @staticmethod
    def _try_cast(value, _type, _default=None):
        try:
            return _type(value)
        except (ValueError, TypeError):
            return _default

    @staticmethod
    def _str2bool(_str, _default=None):
        if isinstance(_str, bool):
            return _str
        elif isinstance(_str, str):
            return _str.lower() in ("true", "1")
        else:
            return _default


class TestConfig(BaseConfig):
    pass


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# DO NOT TOUCH THIS, IT HAS TO BE AT THE END OF THIS FILE
# This configure the config to load on import when running your code.

class ConfigBuilder(object):
    __env_cfg_variable = "BUILDER_CFG_PROFILE"
    __current_config_instance = None
    __current_config_instance_name = None
    __current_config_instance_print = False
    __arg_parser = ArgumentParser(add_help=False)
    __arg_parser.add_argument("-c", "--config", metavar="\"Config Name...\"", help="Configuration Setup", type=str, default=None)

    def __init__(self):
        # Placeholder
        pass

    @staticmethod
    def __get_configs():
        """
        :rtype list[Callable[..., BaseConfig]]
        """
        all_subclasses = []

        def get_all_subclasses(klass):
            """
            :type klass: Callable[..., BaseConfig]
            """
            for subclass in klass.__subclasses__():
                all_subclasses.append(subclass)
                get_all_subclasses(subclass)

        get_all_subclasses(BaseConfig)
        return all_subclasses

    @staticmethod
    def get_config_names():
        """
        :rtype: list[str]
        """
        return [klass.__name__ for klass in ConfigBuilder.__get_configs()]

    @classmethod
    def get_arg_parser(cls):
        """
        :rtype: ArgumentParser
        """
        return cls.__arg_parser

    @classmethod
    def init_config(cls, config_name=None, config_base=None, enable_terminal=True, as_attr_dict=True):
        """
        :type config_name: str | None
        :type config_base: str | None
        :type enable_terminal: bool
        :type as_attr_dict: bool
        """
        if cls.__current_config_instance is None:
            cls.__current_config_instance = cls.get_config(config_name, config_base, enable_terminal, as_attr_dict)

    @classmethod
    def get_config(cls, config_name=None, config_base=None, enable_terminal=True, as_attr_dict=True):
        """
        :type config_name: str | None
        :type config_base: str | None
        :type enable_terminal: bool
        :type as_attr_dict: bool
        :rtype: BaseConfig
        """
        if cls.__current_config_instance is not None and not config_name:
            if not cls.__current_config_instance_print:
                LOGGER.debug("Reusing config instance \"" + str(cls.__current_config_instance_name) + "\"")
                cls.__current_config_instance_print = True
            return ConfigBuilder.__current_config_instance
        if enable_terminal is True:
            terminal_config = getattr(cls.__parse_terminal_config(), "config", None)
            config_name = terminal_config if terminal_config is not None else config_name
        # Check if there's a config profile as an env variable
        config_name = os.getenv(cls.__env_cfg_variable, config_name)
        if config_name is None:
            LOGGER.debug("Using \"BaseConfig\"...")
            config_klass = BaseConfig(root_dir=config_base)
            cls.__current_config_instance = config_klass.as_attr_dict() if as_attr_dict else config_klass
            cls.__current_config_instance_name = config_klass.__class__.__name__
            return cls.__current_config_instance
        for klass in cls.__get_configs():
            if klass.__name__ == config_name:
                LOGGER.debug("Using \"" + config_name + "\" Config...")
                config_klass = klass(root_dir=config_base)
                cls.__current_config_instance = config_klass.as_attr_dict() if as_attr_dict else config_klass
                cls.__current_config_instance_name = config_klass.__class__.__name__
                return cls.__current_config_instance
        LOGGER.debug("Config Provided Not Found, Using \"BaseConfig\"...")
        config_klass = BaseConfig(root_dir=config_base)
        cls.__current_config_instance = config_klass.as_attr_dict() if as_attr_dict else config_klass
        cls.__current_config_instance_name = config_klass.__class__.__name__
        return cls.__current_config_instance

    @classmethod
    def set_config(cls, config_name=None, config_base=None, enable_terminal=True, as_attr_dict=True):
        """
        :type config_name: str | None
        :type config_base: str | None
        :type enable_terminal: bool
        :type as_attr_dict: bool
        """
        if cls.__current_config_instance is None:
            return
        else:
            cls.__current_config_instance = None
            cls.__current_config_instance = cls.get_config(config_name, config_base, enable_terminal, as_attr_dict)

    @classmethod
    def __parse_terminal_config(cls):
        """
        :rtype: argparse.Namespace
        """
        return cls.__arg_parser.parse_known_args()[0]


if __name__ == "__main__":
    pass
