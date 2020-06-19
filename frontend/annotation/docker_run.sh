#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

if [[ -z ${BACKEND_SERVER} ]]; then
    echo ""
    echo ""
    echo ""
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    echo "Please set BACKEND_SERVER environment variable"
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    echo ""
    echo ""
    echo ""
    exit 1
fi

if [[ -z ${SERVER_NAME} ]]; then
    echo ""
    echo ""
    echo ""
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    echo "Please set SERVER_NAME environment variable"
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    echo ""
    echo ""
    echo ""
    exit 1
fi

set -e

export LOG_FORMAT_SNIPPET="${LOG_FORMAT_SNIPPET:-snippets/default-logging.conf}"

envsubst '${BACKEND_SERVER} ${SERVER_NAME} ${LOG_FORMAT_SNIPPET}' < nginx/nlp-web-app > /etc/nginx/sites-available/nlp-web-app

nginx -g 'daemon off;'
