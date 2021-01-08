#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

if [[ $# -lt 3 ]]; then
    echo "Usage: $0 <id> <email/username> <password>"
    exit 1
fi

ID="$1"
USERNAME="$2"
PASSWORD="$3"

export FLASK_APP="pine.backend"
export FLASK_ENV="development"
pipenv run flask add-admin ${ID} ${USERNAME} ${PASSWORD}
