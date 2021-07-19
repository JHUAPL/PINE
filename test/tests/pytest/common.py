# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import json
import os
import sys
import typing

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

TEST_DATA_DIR = os.path.join(DIR, "..", "..", "data")
TEST_USER = "ada"

def client() -> pine.client.LocalPineClient:
    return pine.client.LocalPineClient(BACKEND_BASE_URI, EVE_BASE_URI, MONGO_BASE_URI)

def test_user_data(id_or_email: str = None) -> typing.Union[dict, typing.List[dict]]:
    with open(os.path.join(TEST_DATA_DIR, "users.json"), "r") as f:
        users = json.load(f)
    if id_or_email:
        for user in users:
            if user["_id"] == id_or_email or user["email"] == id_or_email:
                return user
        return None
    else:
        return users

def test_collection_data(title: str = None) -> typing.Union[dict, typing.List[dict]]:
    with open(os.path.join(TEST_DATA_DIR, "collections.json"), "r") as f:
        collections = json.load(f)
    if title:
        for col in collections:
            if "metadata" in col["collection"] and "title" in col["collection"]["metadata"] and \
               col["collection"]["metadata"]["title"] == title:
                return col
        return None
    else:
        return collections

def login_with_user(user_id_or_email: str, client: pine.client.LocalPineClient) -> pine.client.LocalPineClient:
    user = test_user_data(user_id_or_email)
    assert client.is_logged_in() == False
    client.login_eve(user["_id"], user["password"])
    assert client.is_logged_in() == True
    assert client.get_my_user_id() == user["_id"]
    return client

def login_with_test_user(client: pine.client.LocalPineClient) -> pine.client.LocalPineClient:
    return login_with_user(TEST_USER, client)

def get_collection_id(client, collection_title: str) -> str:
    for col in client.list_collections():
        if col["metadata"]["title"] == collection_title:
            return col["_id"]
    raise AssertionError("Couldn't find collection with title " + collection_title)
