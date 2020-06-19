#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

set -x

if [[ -z ${MONGO_PORT} ]]; then
    MONGO_PORT="27018"
fi
export MONGO_PORT
if [[ -z ${FLASK_PORT} ]]; then
    FLASK_PORT="5001"
fi
export FLASK_PORT
pipenv run python3 test/EveClient.py
