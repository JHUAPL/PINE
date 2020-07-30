#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

DIR="$( cd "$( dirname "${0}" )" && pwd )"
source ${DIR}/tests/run_common.sh

set -ex

pushd ${DIR} &> /dev/null
docker build \
    --file docker/cypress/Dockerfile \
    --tag pine/cypress \
    .
popd &> /dev/null

pushd ${DIR}/../ &> /dev/null
docker build \
    --file test/docker/pytest/Dockerfile \
    --tag pine/pytest \
    .
popd &> /dev/null

pushd ${DIR}/../ &> /dev/null
AUTH_MODULE=eve docker-compose ${DOCKER_COMPOSE_FLAGS} build

if [[ $1 != --no-data ]]; then
    AUTH_MODULE=eve EVE_DB_VOLUME=eve_test_db docker-compose ${DOCKER_COMPOSE_FLAGS} up &
    DOCKER_COMPOSE_PID="$!"

    while ! nc -z localhost 8888; do
        sleep 1 
    done
    
    ./setup_docker_test_data.sh

    kill -s SIGINT ${DOCKER_COMPOSE_PID}
    wait ${DOCKER_COMPOSE_PID}
fi

popd &> /dev/null
