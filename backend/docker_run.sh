#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

GUNICORN_CONFIG_FILE="config.py"

if ([[ -z ${AUTH_MODULE} ]] || [[ ${AUTH_MODULE} == "vegas" ]]) && [[ -z ${VEGAS_CLIENT_SECRET} ]]; then
    echo ""
    echo ""
    echo ""
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    echo "Please set VEGAS_CLIENT_SECRET environment variable"
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    echo ""
    echo ""
    echo ""
    exit 1
fi

set -e

/usr/local/bin/gunicorn --config ${GUNICORN_CONFIG_FILE} wsgi:app
