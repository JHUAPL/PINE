#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${DIR}/../.env

export BACKEND_PORT
export EVE_PORT
export MONGO_PORT

if ! wget http://localhost:${BACKEND_PORT}/ping -O /dev/null -o /dev/null || ! wget http://localhost:${EVE_PORT} -O /dev/null -o /dev/null || ! wget http://localhost:${MONGO_PORT} -O /dev/null -o /dev/null; then
    echo "Use docker-compose.test.yml when running docker compose stack."
    exit 1
fi

pushd ${DIR} &> /dev/null

./interactive_dev_run.sh

popd &> /dev/null
