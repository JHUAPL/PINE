# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import json
import logging.config
import os

# make sure this package has been installed
import pythonjsonlogger

CONFIG_FILE_ENV: str = "PINE_LOGGING_CONFIG_FILE"
"""The environment variable that optionally contains the file to use for logging configuration.

:type: str
"""

def setup_logging():
    """Sets up logging, if configured to do so.
    
    The environment variable named by :py:data:`CONFIG_FILE_ENV` is checked and, if present, is
    passed to :py:func:`logging.config.dictConfig`.
    """
    if CONFIG_FILE_ENV not in os.environ:
        return
    file = os.environ[CONFIG_FILE_ENV]
    if os.path.isfile(file):
        with open(file, "r") as f:
            logging.config.dictConfig(json.load(f))
        logging.getLogger(__name__).info("Set logging configuration from file {}".format(file))
