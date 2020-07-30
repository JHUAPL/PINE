#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

if [[ -z ${FRONTEND_BASE_URI} ]] || [[ -z ${BACKEND_BASE_URI} ]]; then
    echo "Set env variables FRONTEND_BASE_URI and BACKEND_BASE_URI"
    exit 1
fi

set -x

while ! wget --no-check-certificate -O /dev/null -o /dev/null ${FRONTEND_BASE_URI}; do
    sleep 1
done

while ! wget -O /dev/null -o /dev/null ${BACKEND_BASE_URI}/ping ; do
    sleep 1
done

sleep 5

cd tests/
pytest pytest/ $@
