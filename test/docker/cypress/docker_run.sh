#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

if [[ $1 == --dashboard ]]; then
    CYPRESS_DASHBOARD="true"
elif [[ $1 == --report ]]; then
    CYPRESS_REPORT="true"
fi

if [[ -z ${CYPRESS_BASE_URL} ]] || [[ -z ${CYPRESS_API_URL} ]]; then
    echo "Set env variables CYPRESS_BASE_URL and CYPRESS_API_URL"
    exit 1
fi

set -ex

CYPRESS_BASE_HOSTNAME=$(echo ${CYPRESS_BASE_URL} | awk -F/ '{print $3}')
if [[ ${CYPRESS_BASE_HOSTNAME} == *_* ]]; then
    # if it has a _, assume it's an invalid hostname and resolve it ahead of time
    CYPRESS_BASE_IP=$(dig +short ${CYPRESS_BASE_HOSTNAME} | awk '{ print ; exit }')
    while [[ -z ${CYPRESS_BASE_IP} ]]; do
        CYPRESS_BASE_IP=$(dig +short ${CYPRESS_BASE_HOSTNAME} | awk '{ print ; exit }')
    done
    CYPRESS_BASE_URL=${CYPRESS_BASE_URL/${CYPRESS_BASE_HOSTNAME}/${CYPRESS_BASE_IP}}
fi

CYPRESS_API_HOSTNAME=$(echo ${CYPRESS_API_URL} | awk -F/ '{print $3}')
if [[ ${CYPRESS_API_HOSTNAME} == *_* ]]; then
    # if it has a _, assume it's an invalid hostname and resolve it ahead of time
    CYPRESS_API_IP=$(dig +short ${CYPRESS_API_HOSTNAME} | awk '{ print ; exit }')
    while [[ -z ${CYPRESS_API_IP} ]]; do
        CYPRESS_API_IP=$(dig +short ${CYPRESS_API_HOSTNAME} | awk '{ print ; exit }')
    done
    CYPRESS_API_URL=${CYPRESS_API_URL/${CYPRESS_API_HOSTNAME}/${CYPRESS_API_IP}}
fi

while ! wget --no-check-certificate -O /dev/null -o /dev/null ${CYPRESS_BASE_URL}; do
    sleep 1
done

sleep 5

cd tests/

export CYPRESS_BASE_URL
export CYPRESS_API_URL

if [[ -n ${CYPRESS_DASHBOARD} ]]; then
    npm run cypress:open
elif [[ -n ${CYPRESS_REPORT} ]]; then
    npm run cypress:report
fi
