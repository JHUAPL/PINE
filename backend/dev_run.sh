#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_FILE="${DIR}/pine/backend/config.py"

if [[ -z ${VEGAS_CLIENT_SECRET} ]]; then
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

export FLASK_APP="pine.backend"
export FLASK_ENV="development"
pipenv run flask run
