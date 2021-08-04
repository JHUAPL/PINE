# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

FROM ubuntu:20.04

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get clean && \
    apt-get -y update && \
    apt-get -y install software-properties-common ca-certificates

RUN apt-get -y update && \
    apt-get -y install \
    dnsutils \
    curl \
    wget \
    netcat \
    jq

# https://docs.cypress.io/guides/continuous-integration/introduction/#Dependencies
RUN apt-get -y update && \
    apt-get install -y \
    libgtk2.0-0 \
    libgtk-3-0 \
    libgbm-dev \
    libnotify-dev \
    libgconf-2-4 \
    libnss3 \
    libxss1 \
    libasound2 \
    libxtst6 \
    xauth \
    xvfb

ARG NODE_VERSION=14
RUN curl -sL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash -
RUN apt-get -y update && \
    apt-get install -y \
    nodejs

RUN mkdir -p /nlp_webapp/ /nlp_webapp/results/videos /nlp_webapp/results/screenshots /nlp_webapp/results/reports /nlp_webapp/results/data
WORKDIR /nlp_webapp/

COPY tests/package*.json tests/
RUN cd tests && npm ci

COPY tests/ ./tests/
RUN rm -rf ./tests/pytest/
COPY docker/cypress/docker_run.sh ./docker_run.sh
COPY data/ ./data/

CMD ["./docker_run.sh", "--dashboard"]
