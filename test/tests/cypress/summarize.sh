#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <report.json>"
    exit 1
fi

REPORT="$1"
STATUS="$(dirname ${REPORT})/status"

set -ex

if [[ $(jq -r '.stats.passPercent' ${REPORT}) == 100 ]]; then
    echo "PASSED" > ${STATUS}
else
    echo "FAILED" > ${STATUS}
fi
