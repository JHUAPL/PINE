#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

command -v git >/dev/null 2>&1
if [[ $? -eq 0 ]]; then
    cd ${DIR}
    git describe --long --dirty --tags --always
else
    echo "unknown-no-git"
fi
