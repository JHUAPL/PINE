#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

export FLASK_APP="pine.backend"
export FLASK_ENV="development"
pipenv run flask reset-user-passwords
