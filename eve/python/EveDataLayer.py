# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import logging.config
import json
import xml.etree.ElementTree as ET

import os
import subprocess
import tempfile

import eve
from flask import jsonify, request, send_file
from flask import __version__ as flask_version
from flask_cors import CORS
from werkzeug import exceptions

from settings import PINE_EVE_VERSION_STR, LOGGER
from Jhed import JHED, JHEDEncoder, JHEDValidator

def post_documents_get_callback(request, payload):
    if "truncate" in request.args:
        truncate = int(request.args.get("truncate", 50))
        if payload.is_json:
            data = payload.get_json()
            if "text" in data:
                data["text"] = data["text"][0 : truncate]
            elif "_items" in data:
                for item in data["_items"]:
                    if "text" in item:
                        item["text"] = item["text"][0 : truncate]
            payload.data = json.dumps(data)
        elif payload.data:
            data = ET.fromstring(payload.data)
            text = data.find("text")
            if text != None:
                text.text = text.text[0 : truncate]
            else:
                for child in data.findall("resource"):
                    text = child.find("text")
                    if text != None and text.text != None:
                        text.text = text.text[0 : truncate]
            payload.data = ET.tostring(data)

def setup_logging():
    if "PINE_LOGGING_CONFIG_FILE" in os.environ and os.path.isfile(os.environ["PINE_LOGGING_CONFIG_FILE"]):
        with open(os.environ["PINE_LOGGING_CONFIG_FILE"], "r") as f:
            logging.config.dictConfig(json.load(f))
        logging.getLogger(__name__).info("Set logging configuration from file {}".format(os.environ["PINE_LOGGING_CONFIG_FILE"]))

def create_app():
    setup_logging()
    
    #app = eve.Eve()
    app = eve.Eve(json_encoder=JHEDEncoder, validator=JHEDValidator)
    app.on_post_GET_documents += post_documents_get_callback

    @app.route("/about", methods = ["GET"])
    def about():
        about = {
            "version": PINE_EVE_VERSION_STR,
            "eve_version": eve.__version__,
            "flask_version": flask_version
        }
        LOGGER.info(about)
        return jsonify(about)

    @app.route("/system/ping", methods=["GET"])
    def ping():
        return jsonify("pong")

    @app.route("/system/export", methods = ["GET"])
    def system_export():
        db = app.data.driver.db
        (f, filename) = tempfile.mkstemp()
        os.close(f)
        cmd = ["mongodump", "--host", db.client.address[0], "--port", str(db.client.address[1]),
               "--gzip", "--archive={}".format(filename)]
        print("RUNNING: {}".format(cmd))
        try:
            output = subprocess.check_output(cmd)
            print(output)
            return send_file(filename, as_attachment = True, attachment_filename = "dump.gz",
                             mimetype = "application/gzip")
        finally:
            os.remove(filename)

    @app.route("/system/import", methods = ["PUT", "POST"])
    def system_import():
        db = app.data.driver.db
        dump_first = request.method.upper() == "POST"
        if not "file" in request.files:
            raise exceptions.UnprocessableEntity("Missing 'file' parameter")
        (f, filename) = tempfile.mkstemp()
        os.close(f)
        try:
            request.files["file"].save(filename)
            cmd = ["mongorestore", "--host", db.client.address[0], "--port", str(db.client.address[1]),
                   "--gzip", "--archive={}".format(filename)]
            if dump_first:
                cmd.append("--drop")
            print("RUNNING: {}".format(cmd))
            output = subprocess.check_output(cmd)
            print(output)
            return jsonify({
                "success": True
            })
        except Exception as e:
            print(e)
            raise exceptions.BadRequest("Error parsing input:" + str(e))
        finally:
            os.remove(filename)

    return app

if __name__ == '__main__':
    app = create_app()
    CORS(app, supports_credentials=True)
    FLASK_PORT = int(os.environ.get("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port = FLASK_PORT)
