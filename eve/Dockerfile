# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

FROM ubuntu:18.04

ARG ROOT_DIR=/nlp-web-app/eve
ARG DB_DIR=/nlp-web-app/eve/db
ARG LOG_DIR=/nlp-web-app/logs/eve
ARG PORT=7510
ARG WORKERS=5

EXPOSE $PORT
# If you want volumes, specify it in docker-compose

ENV DEBIAN_FRONTEND noninteractive
ENV FLASK_PORT $PORT
ENV DB_DIR $DB_DIR
ENV LOG_DIR $LOG_DIR

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

RUN mkdir -p $ROOT_DIR $DB_DIR $LOG_DIR

# Install dependencies
RUN apt-get clean && \
    apt-get -y update && \
    apt-get -y install software-properties-common

RUN apt-get -y update && \
    apt-get -y install git build-essential python3.6 python3-pip gettext-base && \
    pip3 install --upgrade pip gunicorn pipenv

# Install latest mongodb
RUN if [ -n "${DB_DIR}" ] ; then \
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 9DA31620334BD75D9DCB49F368818C72E52529D4 && \
    echo "deb [ arch=amd64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/4.0 multiverse" > /etc/apt/sources.list.d/mongodb-org-4.0.list && \
    apt-get -y update && \
    apt-get install -y mongodb-org mongodb-org-server mongodb-org-tools mongodb-org-shell; \
    fi

# Install python packages
WORKDIR $ROOT_DIR
ADD Pipfile Pipfile.lock ./
RUN pipenv install --system --deploy

# Add eve and code
ADD docker/wsgi.py $ROOT_DIR
ADD docker_run.sh $ROOT_DIR
ADD test/ $ROOT_DIR/test

ADD python/ $ROOT_DIR/python

COPY docker/config.py.template ./
RUN PORT=$PORT WORKERS=$WORKERS envsubst '${PORT} ${WORKERS}' < ./config.py.template > ./config.py

# Start MongoDB and the Eve Service
CMD ["./docker_run.sh"]
