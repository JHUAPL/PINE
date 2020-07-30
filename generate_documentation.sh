#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

pushd ${DIR}/docs &>/dev/null
pipenv run doc
popd &>/dev/null

echo "See documentation in docs/build."
