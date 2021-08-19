# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import logging
import os
import sys

from . import log
log.setup_logging()

from flask import Flask, abort, jsonify, redirect, render_template, request, send_file
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
    app = Flask(__name__, instance_relative_config=True, template_folder="api/swagger-ui")
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

    @app.route("/openapi.yaml", methods=["GET"])
    def openapi_spec():
        # Specify statically where the openapi file is, relative path
        return send_file("api/openapi.yaml", mimetype='text/yaml', as_attachment=False)

    @app.route("/swagger", methods=["GET"], strict_slashes=False)
    def swagger_ui_index():
        # forward to /api/ui/index.html, taking proxy prefix into account if set
        url = request.headers.get("X-Forwarded-Prefix", "") + "/swagger/index.html"
        LOGGER.info("Redirecting to {}".format(url))
        return redirect(url)

    @app.route("/swagger/<file>", methods=["GET"])
    def swagger_ui(file: str):
        if file == "index.html":
            # get url for /api/openapi.yaml, taking proxy prefix into account if set
            url = request.headers.get("X-Forwarded-Prefix", "") + "/openapi.yaml"
            LOGGER.info("Grabbing spec from {}".format(url))
            return render_template("index.html", spec_url=url)
        else:
            return send_file("api/swagger-ui/{}".format(file))

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

    if app.env == "development":
        # if running dev stack, map /api/<rule> to <rule>
        for rule in app.url_map.iter_rules():
            if rule.rule.startswith("/api"):
                continue
            rule_copy = rule.empty()
            rule_copy.rule = "/api" + rule_copy.rule
            app.url_map.add(rule_copy)

    return app
