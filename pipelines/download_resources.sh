#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

OPENNLP_VERSION=${OPENNLP_VERSION:-1.9.0}
CORENLP_VERSION=${CORENLP_VERSION:-2018-02-27}

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RESOURCES_DIR=${DIR}/pine/pipelines/resources

pushd ${RESOURCES_DIR} &> /dev/null

set -x

if [[ ! -d apache-opennlp-${OPENNLP_VERSION} ]]; then
    if [[ ! -f apache-opennlp-${OPENNLP_VERSION}-bin.tar.gz ]]; then
        wget https://archive.apache.org/dist/opennlp/opennlp-${OPENNLP_VERSION}/apache-opennlp-${OPENNLP_VERSION}-bin.tar.gz
    fi
    tar xzf apache-opennlp-${OPENNLP_VERSION}-bin.tar.gz
fi
if [[ ! -f apache-opennlp-${OPENNLP_VERSION}/en-sent.bin ]]; then
    wget http://opennlp.sourceforge.net/models-1.5/en-sent.bin -O apache-opennlp-${OPENNLP_VERSION}/en-sent.bin
fi
if [[ ! -f apache-opennlp-${OPENNLP_VERSION}/en-token.bin ]]; then
    wget http://opennlp.sourceforge.net/models-1.5/en-token.bin -O apache-opennlp-${OPENNLP_VERSION}/en-token.bin
fi

if [[ ! -d stanford-corenlp-full-${CORENLP_VERSION} ]]; then
    if [[ ! -f stanford-corenlp-full-${CORENLP_VERSION}.zip ]]; then
        wget http://nlp.stanford.edu/software/stanford-corenlp-full-${CORENLP_VERSION}.zip
    fi
    unzip stanford-corenlp-full-${CORENLP_VERSION}.zip
fi

if ! [[ -d stanford-ner-${CORENLP_VERSION} ]]; then
    if [[ ! -f stanford-ner-${CORENLP_VERSION}.zip ]]; then
        wget https://nlp.stanford.edu/software/stanford-ner-${CORENLP_VERSION}.zip
    fi
    unzip stanford-ner-${CORENLP_VERSION}.zip
fi

popd &> /dev/null
