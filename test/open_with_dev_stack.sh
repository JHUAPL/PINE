#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

DIR="$( cd "$( dirname "${0}" )" && pwd )"
source ${DIR}/tests/run_common.sh

pushd ${DIR}/tests
pipenv run pytest pytest/ &
PYTEST_PID="$!"
npm run cypress:open -- --config-file cypress.dev.json &
CYPRESS_PID="$!"
popd

wait ${PYTEST_PID} ${CYPRESS_PID}
