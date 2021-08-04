# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import logging

from flask import redirect, render_template, request, send_file, url_for, Blueprint

bp = Blueprint("api", __name__, url_prefix = "/api", template_folder="swagger-ui")
LOGGER = logging.getLogger(__name__)

# Return the openapi specification for SwaggerUI
@bp.route("/openapi.yaml", methods=["GET"])
def openapi_spec():
    # Specify statically where the openapi file is, relative path
    return send_file("api/openapi.yaml", mimetype='text/yaml', as_attachment=False)

@bp.route("/ui", methods=["GET"], strict_slashes=False)
def swagger_ui_index():
    # forward to /api/ui/index.html, taking proxy prefix into account if set
    url = request.headers.get("X-Forwarded-Prefix", "") + url_for("api.swagger_ui", file="index.html")
    LOGGER.info("Redirecting to {}".format(url))
    return redirect(url)

@bp.route("/ui/<file>", methods=["GET"])
def swagger_ui(file: str):
    if file == "index.html":
        # get url for /api/openapi.yaml, taking proxy prefix into account if set
        url = request.headers.get("X-Forwarded-Prefix", "") + url_for("api.openapi_spec")
        LOGGER.info("Grabbing spec from {}".format(url))
        return render_template("index.html", spec_url=url)
    else:
        return send_file("api/swagger-ui/{}".format(file))

def init_app(app):
    app.register_blueprint(bp)
