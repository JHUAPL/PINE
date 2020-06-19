#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

DIR="$( cd "$( dirname "${0}" )" && pwd )"
DATA_DIR=${DATA_DIR:-${DIR}}
LOG_DIR=${LOG_DIR:-${DIR}/logs}
DB_DIR=${DATA_DIR}/db

set -ex

mkdir -p ${DB_DIR} ${LOG_DIR}

# use a port separate from the system-wide mongo port, if it's running as a service
if [[ -z ${MONGO_PORT} ]]; then
    MONGO_PORT="27018"
fi
export MONGO_PORT
mkdir -p logs/ db/
mongod --dbpath ${DB_DIR} \
       --port ${MONGO_PORT} \
       --logpath ${LOG_DIR}/mongod.log \
       --logRotate reopen --logappend &

if [[ -z ${FLASK_PORT} ]]; then
    FLASK_PORT="5001"
fi
export FLASK_PORT

export FLASK_ENV="development"
export PYTHONPATH="${DIR}/python"
pipenv run python3 ${DIR}/python/EveDataLayer.py
