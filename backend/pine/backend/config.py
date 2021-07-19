# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import os

# default configuration values

SECRET_KEY = "Cq13XII=%"
DEBUG = True

if os.environ.get("EVE_SERVER"):
    EVE_SERVER = os.environ.get("EVE_SERVER")
elif os.environ.get("FLASK_ENV") and os.environ.get("FLASK_ENV").startswith("dev"):
    EVE_SERVER = "http://localhost:5001"
else:
    EVE_SERVER = "http://eve:7510"

if os.environ.get("REDIS_SERVER"):
    REDIS_SERVER = os.environ.get("REDIS_SERVER")
elif os.environ.get("FLASK_ENV") and os.environ.get("FLASK_ENV").startswith("dev"):
    REDIS_SERVER = "localhost"
else:
    REDIS_SERVER = "redis"

REDIS_PORT = int(os.environ.get("REDIS_PORT", 6479))

AUTH_MODULE = os.environ.get("AUTH_MODULE", "vegas")
if not AUTH_MODULE: AUTH_MODULE = "vegas"

# default VEGAS to stage
VEGAS_SERVER = os.environ.get("VEGAS_SERVER", "https://slife.jh.edu")
VEGAS_CLIENT_ID = os.environ.get("VEGAS_CLIENT_ID", "1976d9d4-be86-44ce-aa0f-c5a4b295c701")
VEGAS_CLIENT_SECRET = os.environ.get("VEGAS_CLIENT_SECRET", None)

DOCUMENT_IMAGE_DIR = os.environ.get("DOCUMENT_IMAGE_DIR", "/mnt/azure")
