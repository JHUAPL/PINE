#!/bin/bash
# (C) 2021 The Johns Hopkins University Applied Physics Laboratory LLC.

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Find all blueprint-specs.
BP_SPECS=$(cd backend/pine/backend && find . -name 'openapi.yaml' | grep -v './api/openapi.yaml' | sort | awk '{print "/local/" $0}')

set -ex

# Join them into one.
docker run --rm \
    -v "${DIR}/backend/pine/backend:/local:rw" \
    -w /local/api \
    redocly/openapi-cli join \
        /local/api/base.yaml \
        ${BP_SPECS}

# Dereference and lint.
docker run --rm -v "${DIR}/backend/pine/backend:/local:rw" redocly/openapi-cli bundle \
    --lint \
    --dereferenced \
    --output /local/api/openapi.yaml \
    /local/api/openapi.yaml

# docker run --rm -v "${DIR}/backend/pine/backend:/local:rw" openapitools/openapi-generator-cli generate \
#     -g openapi-yaml \
#     -i /local/api/openapi.yaml -o /local/api \
#     --additional-properties outputFile=openapi.yaml \
#     $@

sed -i '1i # (C) 2021 The Johns Hopkins University Applied Physics Laboratory LLC.\n' ${DIR}/backend/pine/backend/api/openapi.yaml