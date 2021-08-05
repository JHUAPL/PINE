#!/bin/bash
# (C) 2021 The Johns Hopkins University Applied Physics Laboratory LLC.

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo "Checking dependencies for security issues..."

for MOD in backend client docs eve pipelines test; do
    pushd ${DIR}/${MOD} &> /dev/null
    echo ""
    echo "    Checking ${MOD}..."
    pipenv check
    popd &> /dev/null
done

for MOD in frontend/annotation test/tests; do
    pushd ${DIR}/${MOD} &> /dev/null
    echo ""
    echo "    Checking ${MOD}..."
    npm audit
    popd &> /dev/null
done
