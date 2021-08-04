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

ARG ROOT_DIR=/nlp-web-app/eve
ARG DB_DIR=/nlp-web-app/eve/db
ARG LOG_DIR=/nlp-web-app/logs/eve
ARG PORT=7510
ARG WORKERS=5
ARG MONGO_PORT=27018

EXPOSE $PORT
EXPOSE $MONGO_PORT
# If you want volumes, specify it in docker-compose

ENV FLASK_PORT $PORT
ENV DB_DIR $DB_DIR
ENV LOG_DIR $LOG_DIR

RUN mkdir -p $ROOT_DIR $DB_DIR $LOG_DIR

# Install pipenv
RUN apt-get -y update && \
    apt-get -y install git build-essential python3.6 python3-pip gettext-base

RUN pip3 install --default-timeout=30 --upgrade pip gunicorn pipenv

# Install latest mongodb
# It can no longer be installed from packages due to the packages relying on systemctl which is not
#   in the Ubuntu docker image.
# https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu-tarball/
ARG MONGO_VERSION=ubuntu1804-4.2.11
RUN if [ -n "${DB_DIR}" ] ; then \
    apt-get -y install libcurl4 openssl liblzma5 wget && \
    wget --progress=dot https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-${MONGO_VERSION}.tgz && \
    tar xzf mongodb-linux-x86_64-${MONGO_VERSION}.tgz && \
    mv mongodb-linux-x86_64-${MONGO_VERSION}/bin/* /usr/local/bin/; \
    fi

# Install python packages
WORKDIR $ROOT_DIR
ADD Pipfile Pipfile.lock ./
RUN REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt pipenv install --dev --system --deploy

# Add eve and code
ADD docker/wsgi.py $ROOT_DIR
ADD docker_run.sh $ROOT_DIR

ADD python/ $ROOT_DIR/python

COPY docker/config.py.template ./
RUN PORT=$PORT WORKERS=$WORKERS MONGO_PORT=${MONGO_PORT} envsubst '${PORT} ${WORKERS} ${MONGODB_PORT}' < ./config.py.template > ./config.py

# Start MongoDB and the Eve Service
CMD ["./docker_run.sh"]
