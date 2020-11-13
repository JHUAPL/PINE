#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 [--build|--up|--up-test]"
    echo "       --build will build the docker stack"
    echo "       --up will bring up the docker stack"
    echo "       --up-test will bring up the docker stack with the testing ports exposed"
    echo "       --down will bring down the docker stack"
    exit 1
fi
COMMAND="$1"
shift

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ${DIR}

set -x

export PINE_VERSION=$(./version.sh)
if [[ ${COMMAND} == --build ]]; then
    docker-compose build $@
elif [[ ${COMMAND} == --up ]]; then
    docker-compose up --abort-on-container-exit $@
elif [[ ${COMMAND} == --up-test ]]; then
    docker-compose \
        -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.test.yml \
        up --abort-on-container-exit $@
elif [[ ${COMMAND} == --down ]]; then
    docker-compose down $@
fi
