#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

set -x

export MONGO_PORT=${MONGO_PORT:-27018}
export EVE_PORT=${EVE_PORT:-5001}
export BACKEND_PORT=${BACKEND_PORT:-5000}

export PINE_LOGGING_CONFIG_FILE=$(realpath ${DIR}/../shared/logging.python.dev.json)

pushd ${DIR} &>/dev/null
pipenv install
pipenv run python3 ./data/import_test_data.py
popd &>/dev/null
