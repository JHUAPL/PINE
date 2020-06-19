#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

DIR="$( cd "$( dirname "${0}" )" && pwd )"
DATA_DIR=${DATA_DIR:-${DIR}/data}
LOG_DIR=${LOG_DIR:-${DIR}/logs}

set -ex

if [[ -z ${REDIS_PORT} ]]; then
    REDIS_PORT="6379"
fi

mkdir -p ${DATA_DIR} ${LOG_DIR}

redis-server conf/redis.conf \
    --port ${REDIS_PORT} \
    --include ${LOG_FORMAT_SNIPPET:-conf/default-logging.conf} \
    --dir ${DATA_DIR} \
    --logfile ${LOG_DIR}/redis-server.log \
    --daemonize no
