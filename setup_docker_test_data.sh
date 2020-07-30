#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

DIR="$( cd "$( dirname "${0}" )" && pwd )"
source ${DIR}/.env

export PINE_VERSION=$(${DIR}/version.sh)

set -ex

if ! nc -z localhost ${EVE_PORT} || ! nc -z localhost ${MONGO_PORT} || ! nc -z localhost ${BACKEND_PORT} || ! wget -O /dev/null -o /dev/null http://localhost:${BACKEND_PORT}/ping; then   
    echo "Please run docker-compose up using docker-compose.test.yml."
    exit 1
fi

export BACKEND_PORT
export EVE_PORT
export MONGO_PORT

pushd ${DIR}/test &> /dev/null
./setup_test_data.sh
popd &> /dev/null
