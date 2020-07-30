#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

DIR="$( cd "$( dirname "${0}" )" && pwd )"

set -e

if [[ -z ${MONGO_URI} ]] && [[ -z ${DB_DIR} ]]; then
    echo "Please set MONGO_URI or DB_DIR in docker configuration."
    exit 1
fi

if [[ -n ${MONGO_URI} ]]; then
    export MONGO_URI
fi
if [[ -n ${FLASK_PORT} ]]; then
    export FLASK_PORT
    export MONGO_PORT=${MONGO_PORT:-27018}
fi

mkdir -p ${LOG_DIR}

if [[ -z ${MONGO_URI} ]]; then
    DOCKER_IP=$(awk 'END{print $1}' /etc/hosts)
    
    # only run if MONGO_URI is not set
    mongod --dbpath ${DB_DIR} \
           --logpath ${LOG_DIR}/mongod.log \
           --bind_ip localhost,${DOCKER_IP} \
           --port ${MONGO_PORT} \
           --logRotate reopen --logappend &
fi
/usr/local/bin/gunicorn --config config.py --pythonpath ${DIR}/python wsgi:app
