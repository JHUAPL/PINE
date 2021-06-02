#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

usage() {
    set +x
    echo "Usage: $0 [--build|--build-with-cert <cert file>|--up|--up-test]"
    echo "       --build will build the docker stack"
    echo "       --build-with-certs <crt file> will build the docker stack using the given SSL certificate file"
    echo "       --up will bring up the docker stack"
    echo "       --up-test will bring up the docker stack with the testing ports exposed"
    echo "       --down will bring down the docker stack"
}

if [[ $# -lt 1 ]]; then
    usage
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
elif [[ ${COMMAND} == --build-with-cert ]]; then
    if [[ -z $1 ]]; then
        usage
        exit 1
    fi
    if [[ ! -f $1 ]]; then
        echo "File $1 doesn't exist."
        exit 2
    fi
    cp $1 eve/docker/host.crt
    cp $1 backend/docker/host.crt
    cp $1 frontend/annotation/docker/host.crt
    cp $1 pipelines/docker/host.crt
    shift
    docker-compose build $@
    rm eve/docker/host.crt backend/docker/host.crt frontend/annotation/docker/host.crt pipelines/docker/host.crt
elif [[ ${COMMAND} == --up ]]; then
    docker-compose up --abort-on-container-exit $@
elif [[ ${COMMAND} == --up-test ]]; then
    docker-compose \
        -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.test.yml \
        up --abort-on-container-exit $@
elif [[ ${COMMAND} == --down ]]; then
    docker-compose down $@
else
    usage
    exit 1
fi
