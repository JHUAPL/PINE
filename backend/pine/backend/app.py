# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import logging
import os
import sys

from . import log
log.setup_logging()

from flask import Flask, abort, jsonify
from flask import __version__ as flask_version
from werkzeug import exceptions

from . import config

VERSION = os.environ.get("PINE_VERSION", "unknown-no-env")
LOGGER = logging.getLogger(__name__)

def handle_error(e):
    logging.getLogger(__name__).error(e, exc_info=True)
    sys.stdout.flush()
    sys.stderr.flush()
    return jsonify(str(e.description)), e.code

def handle_uncaught_exception(e):
    if isinstance(e, exceptions.InternalServerError):
        original = getattr(e, "original_exception", None)
        if original is None:
            logging.getLogger(__name__).error(e, exc_info=True)
        else:
            logging.getLogger(__name__).error(original, exc_info=True)
        return jsonify(e.description), e.code
    elif isinstance(e, exceptions.HTTPException):
        return handle_error(e)
    else:
        logging.getLogger(__name__).error(e, exc_info=True)
        return jsonify(exceptions.InternalServerError.description), exceptions.InternalServerError.code

def create_app(test_config = None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config)

    app.register_error_handler(exceptions.HTTPException, handle_error)
    app.register_error_handler(Exception, handle_uncaught_exception)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/ping")
    def ping():
        return jsonify("pong")

    from .data import service as service
    @app.route("/about")
    def about():
        resp = service.get("about")
        if not resp.ok:
            abort(resp.status)
        about = {
            "version": VERSION,
            "flask_version": flask_version,
            "db": resp.json()
        }
        LOGGER.info("Eve service performance history:")
        LOGGER.info(service.PERFORMANCE_HISTORY.pformat())
        LOGGER.info("Version information:")
        LOGGER.info(about)
        return jsonify(about)

    from . import cors
    cors.init_app(app)

    from .auth import bp as authbp
    authbp.init_app(app)

    from .data import bp as databp
    databp.init_app(app)

    from .collections import bp as collectionsbp
    collectionsbp.init_app(app)

    from .documents import bp as documentsbp
    documentsbp.init_app(app)

    from .annotations import bp as annotationsbp
    annotationsbp.init_app(app)

    from .admin import bp as adminbp
    adminbp.init_app(app)

    from .pipelines import bp as pipelinebp
    pipelinebp.init_app(app)

    from .pineiaa import bp as iaabp
    iaabp.init_app(app)

    return app
