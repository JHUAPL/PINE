#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

BACKEND_PORT=${BACKEND_PORT:-5000}
EVE_PORT=${EVE_PORT:-5001}
MONGO_PORT=${MONGO_PORT:-27018}

pushd ${DIR} &> /dev/null

read -r -d '' CODE << EOF
import code;
import sys;

sys.path.append("${DIR}");
import pine.client;
pine.client.setup_logging();
client = pine.client.LocalPineClient("http://localhost:${BACKEND_PORT}", "http://localhost:${EVE_PORT}", "mongodb://localhost:${MONGO_PORT}");
code.interact(banner="",exitmsg="",local=locals())
EOF

echo "${CODE}"
echo ""
PINE_LOGGING_CONFIG_FILE=$(realpath ${DIR}/../shared/logging.python.dev.json) pipenv run python3 -c "${CODE}"

popd &> /dev/null
