#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

set -ex

pushd backend &> /dev/null
pipenv install --dev
popd &> /dev/null

pushd eve &> /dev/null
sudo apt-get install -y mongodb-server
if which systemctl ; then
    sudo systemctl stop mongodb
    sudo systemctl disable mongodb
fi
rm -rf db/
pipenv install --dev
popd &> /dev/null

pushd frontend/annotation &> /dev/null
npm install
popd &> /dev/null

pushd pipelines &> /dev/null
sudo apt-get install -y default-jdk
pipenv install --dev
popd &> /dev/null

pushd redis &> /dev/null
sudo apt-get install -y redis-server
if which systemctl ; then
    sudo systemctl stop redis-server
    sudo systemctl disable redis-server
fi
popd &> /dev/null

pushd test &> /dev/null
pipenv install --dev
popd &> /dev/null

pushd test/tests &> /dev/null
npm install
popd &> /dev/null

pushd client &> /dev/null
pipenv install --dev
popd &> /dev/null
