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

# For Controlling Startup Behaviour
ENV SKIP_PERMISSION_FIX 0

# Set Pipeline of interest
ENV PIPELINE $PIPELINE

# Set environment variables associated with click, necessary for use with pipenv?
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Configure Container Default User
RUN groupadd -r nlp_user && useradd -m -r -g nlp_user nlp_user

# Configure GOSU (https://github.com/tianon/gosu)
COPY docker/gosu-110-amd64.bin /usr/local/bin/gosu
RUN chmod +x /usr/local/bin/gosu \
    && sync \
    && gosu nobody true

# Configure Tini (https://github.com/krallin/tini)
COPY docker/tini-static-amd64.bin /usr/local/bin/tini
RUN chmod +x /usr/local/bin/tini \
    && sync

# Install OS Dependencies
RUN set -ex \
    && apt-get update \
    && apt-get --no-install-recommends --yes install \
    build-essential \
    git curl wget iputils-ping net-tools dnsutils \
    htop tmux vim nano screen zsh \
    libgdal-dev gdal-bin \
    && apt-get -y autoremove \
    && apt-get -y clean \
    && rm -rf /var/lib/apt/lists/*

#install python
RUN apt-get update && apt-get install -y \
    python3.6 \
    python3-pip \
    python3-setuptools \
    python3-dev

# Installing spacy requires a lot of memory, need to kill running docker containers or it will fail here on my machine
# upgrade pip install/upgrade pipenv
RUN pip3 install --default-timeout=30 --upgrade pip pipenv

#Only corenlp/opennlp require java so add later on
RUN apt-get update && apt-get install -y \
    openjdk-8-jdk


# TODO: Will need to refactor all directories in this Dockerfile once we adjust project structure
ARG ROOT_DIR=/nlp-web-app/pipelines
ENV ROOT_DIR ${ROOT_DIR}
RUN mkdir -p ${ROOT_DIR}
WORKDIR ${ROOT_DIR}

# pipenv causing container to fail to rebuild if spacy installed previously
#Install python requirements
COPY Pipfile Pipfile.lock ./
RUN REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt pipenv install --dev --system --deploy


#Copy contents of pipeline folder to docker
COPY pine ./pine

# ensure that /opt/ is writable regardless of the UID our ctp instance ends up having at runtime
RUN chown -R nlp_user:nlp_user ${ROOT_DIR} \
    && chmod g+s ${ROOT_DIR} \
    && sync

# Copy Entrypoint Script
COPY docker/docker-entrypoint.sh /usr/local/bin/

## Copy the current directory contents into the container at /opt (order matters for cache/speed)
#COPY models/ /opt/models/
#COPY service/ /opt/service/
#COPY app/ /opt/app/
#COPY run_service.py /opt/
#COPY config.yaml /opt/

# Execute and Backwards Compat
RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
    && sync \
    && ln -s /usr/local/bin/docker-entrypoint.sh /entrypoint.sh

# Declare Volumes
VOLUME ["/opt/logs"]

# Declare Entrypoint
ENTRYPOINT ["/usr/local/bin/tini", "--", "docker-entrypoint.sh"]

# Set PYTHONPATH
ENV PYTHONPATH "${PYTHONPATH}:/"

# Run app.py when the container launches
COPY docker_run.sh ./
CMD ["./docker_run.sh"]
