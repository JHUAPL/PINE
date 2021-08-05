#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

DIR="$( cd "$( dirname "${0}" )" && pwd )"
source ${DIR}/tests/run_common.sh

if [[ $1 == --pytest ]]; then
    pushd ${DIR}/tests
    pipenv run pytest pytest/ &
    PYTEST_PID="$!"
    popd
    wait ${PYTEST_PID}
elif [[ $1 == --cypress ]]; then
    pushd ${DIR}/tests
    npm run cypress:open -- --config-file cypress.dev.json &
    CYPRESS_PID="$!"
    popd
    wait ${CYPRESS_PID}
else
    echo "Usage: $0 [--pytest|--cypress]"
    exit 1
fi
