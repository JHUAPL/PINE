#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

set -x

pushd eve &> /dev/null
./setup_dev_data.sh
popd &> /dev/null

pushd backend &> /dev/null
./setup_dev_data.sh
popd &> /dev/null

pushd eve/python &> /dev/null
python3 update_documents_annnotation_status.py
popd &> /dev/null
