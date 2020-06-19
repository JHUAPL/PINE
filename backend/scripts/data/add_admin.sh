#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <username> <password>"
    exit 1
fi

USERNAME="$1"
PASSWORD="$2"

export FLASK_APP="pine.backend"
export FLASK_ENV="development"
pipenv run flask add-admin ${USERNAME} ${PASSWORD}
