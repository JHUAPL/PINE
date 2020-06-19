#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [[ -n ${DATA_DIR} ]]; then
    export AL_ROOT_DIR=${DATA_DIR}
    mkdir -p ${DATA_DIR}/models ${DATA_DIR}/tmp
fi

set -x

PIDS=""
for SERVICE in opennlp corenlp spacy; do
    AL_PIPELINE=${SERVICE} pipenv run python3 -m pine.pipelines.run_service &
    PIDS="${PIDS} $!"
done

for PID in ${PIDS}; do
    wait ${PID}
done
