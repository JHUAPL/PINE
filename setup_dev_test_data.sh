#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

set -x

pushd test &> /dev/null
./setup_test_data.sh
popd &> /dev/null
