# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import os
import sys

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(DIR)
if os.path.isdir(os.path.join(DIR, "..", "..", "client")): # docker container
    sys.path.append(os.path.join(DIR, "..", "..", "client"))
if os.path.isdir(os.path.join(DIR, "..", "..", "..", "client")): # dev stack
    sys.path.append(os.path.join(DIR, "..", "..", "..", "client"))

import pine.client

MONGO_BASE_URI = os.environ.get("MONGO_BASE_URI", "mongodb://localhost:27018")
EVE_BASE_URI = os.environ.get("EVE_BASE_URI", "http://localhost:5001")
BACKEND_BASE_URI = os.environ.get("BACKEND_BASE_URI", "http://localhost:5000")

def client():
    return pine.client.LocalPineClient(BACKEND_BASE_URI, EVE_BASE_URI, MONGO_BASE_URI)
