# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

FROM ubuntu:18.04

ARG PORT=6379
ARG ROOT_DIR=/nlp-web-app/redis
ARG DATA_DIR=/nlp-web-app/redis/data
ARG LOG_DIR=/nlp-web-app/logs/redis

ARG REDIS_ETC=/etc/redis

EXPOSE $PORT
VOLUME ["$DATA_DIR"]
# log volume is handled in docker-compose

ENV PORT $PORT
ENV LOG_DIR $LOG_DIR
ENV DATA_DIR $DATA_DIR
ENV CONF_FILE $REDIS_ETC/redis.conf

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

RUN mkdir -p $ROOT_DIR $LOG_DIR $DATA_DIR
RUN apt-get update -y && \
    apt-get install -y redis-server

ADD conf/redis.conf conf/default-logging.conf $REDIS_ETC/
ADD docker_run.sh $ROOT_DIR

WORKDIR $ROOT_DIR

CMD ["./docker_run.sh"]
