# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

from flask import request
from flask_cors import CORS

def not_found(e):
    # because of CORS, we weren't properly getting the 404 because of the pre-flight OPTIONS
    # so return 200 for pre-flight check and let the actual get/post/whatever get a 404 that can
    # be read with CORS
    if request.method.upper() == "OPTIONS":
        return "Page not available but this is only a pre-flight check", 200
    return e

def init_app(app):
    CORS(app, supports_credentials = True)
    app.register_error_handler(404, not_found)
        
