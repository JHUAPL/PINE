#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

DIR="$( cd "$( dirname "${0}" )" && pwd )"
. ${DIR}/tests/run_common.sh

setup $@

if [[ -n ${PINE_LOGGING_CONFIG_FILE} ]]; then
    export PINE_LOGGING_CONFIG_FILE
fi

docker-compose ${DOCKER_COMPOSE_FLAGS} up &
DOCKER_COMPOSE_PID="$!"

while ! docker network inspect nlp_webapp_default &> /dev/null; do
    sleep 1
done

if [[ -n ${PYTEST} ]]; then
    docker run -it \
        --name pine-pytest \
        --network nlp_webapp_default \
        --env FRONTEND_BASE_URI="https://frontend_annotation" \
        --env MONGO_BASE_URI="mongodb://eve:27018" \
        --env EVE_BASE_URI="http://eve:7510" \
        --env BACKEND_BASE_URI="http://backend:7520" \
        --volume=/etc/localtime:/etc/localtime:ro \
        pine/pytest
    TEST_EXIT_CODE="$?"
else
    docker run -it \
        --name pine-cypress \
        --network nlp_webapp_default \
        --env AUTH_MODULE="${AUTH_MODULE}" \
        --env CYPRESS_BASE_URL="https://frontend_annotation" \
        --env CYPRESS_API_URL="https://frontend_annotation/api" \
        --volume=/etc/localtime:/etc/localtime:ro \
        ${DOCKER_ARGS} \
        pine/cypress ${COMMAND}
    TEST_EXIT_CODE="$?"
fi

kill -s SIGINT ${DOCKER_COMPOSE_PID}
wait ${DOCKER_COMPOSE_PID}

cleanup $@

if [[ -n ${PYTEST} ]]; then
    docker rm pine-pytest
else
    docker rm pine-cypress
fi

check_passed $@

exit ${TEST_EXIT_CODE}
