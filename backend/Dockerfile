# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

FROM ubuntu:20.04

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND noninteractive

# Install basic dependencies
RUN apt-get clean && \
    apt-get -y update && \
    apt-get -y install software-properties-common ca-certificates

# Copy any certs
COPY docker/*.crt /usr/local/share/ca-certificates/
RUN rm /usr/local/share/ca-certificates/empty.crt && update-ca-certificates

# Install pipenv
RUN apt-get -y update && \
    apt-get -y install git build-essential python3.6 python3-pip gettext-base

RUN pip3 install --default-timeout=30 --upgrade pip gunicorn pipenv

ARG ROOT_DIR=/nlp-web-app/backend
ARG REDIS_PORT=6379
ARG PORT=7520
ARG WORKERS=5

EXPOSE $PORT

ENV REDIS_PORT $REDIS_PORT

RUN mkdir -p $ROOT_DIR

ADD Pipfile $ROOT_DIR
ADD Pipfile.lock $ROOT_DIR

WORKDIR $ROOT_DIR
RUN REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt pipenv install --dev --system --deploy

ADD pine/ $ROOT_DIR/pine/
ADD scripts/ $ROOT_DIR/scripts/

ADD docker/wsgi.py $ROOT_DIR/
ADD docker_run.sh $ROOT_DIR/

COPY docker/config.py.template ./
RUN PORT=$PORT WORKERS=$WORKERS envsubst '${PORT} ${WORKERS}' < ./config.py.template > ./config.py

CMD ["./docker_run.sh"]
