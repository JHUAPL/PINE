#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

set -e

mkdir -p ${LOG_DIR}
redis-server ${CONF_FILE} \
    --include ${LOG_FORMAT_SNIPPET:-/etc/redis/default-logging.conf} \
    --port ${PORT} \
    --daemonize no \
    --dir ${DATA_DIR}
