#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

set -x

docker-compose exec eve python3 test/EveClient.py
docker-compose exec backend scripts/data/reset_user_passwords.sh
docker-compose exec eve python3 python/update_documents_annnotation_status.py
