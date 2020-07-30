# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

FROM ubuntu:18.04

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get clean && \
    apt-get -y update && \
    apt-get -y install software-properties-common

RUN apt-get -y update && \
    apt-get -y install git build-essential curl jq wget ruby gettext-base && \
    gem install mustache

RUN wget https://nginx.org/keys/nginx_signing.key && \
    apt-key add nginx_signing.key && \
    rm nginx_signing.key && \
    echo "deb https://nginx.org/packages/ubuntu/ bionic nginx" && \
    apt-get -y remove nginx* && \
    apt-get -y update && \
    apt-get -y install nginx

ARG NODE_VERSION=12

RUN curl -sL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash -
RUN apt-get -y update && \
    apt-get install -y nodejs

ARG ROOT_DIR=/nlp-web-app/frontend
ARG SERVER_TYPE=http

EXPOSE 80 443

RUN mkdir -p $ROOT_DIR
WORKDIR $ROOT_DIR

ADD angular.json $ROOT_DIR/
ADD package*.json $ROOT_DIR/

RUN npm install

ADD e2e/ $ROOT_DIR/e2e
ADD nginx/ $ROOT_DIR/nginx
ADD tsconfig.json $ROOT_DIR/
ADD tslint.json $ROOT_DIR/

RUN mkdir -p /etc/ssl/private/ /etc/ssl/certs/ /etc/nginx/snippets/
ADD nginx/certs/server.key /etc/ssl/private/
ADD nginx/certs/server.crt /etc/ssl/certs/
ADD nginx/certs/dhparam.pem /etc/nginx/
ADD nginx/snippets/* /etc/nginx/snippets/

RUN echo "---" > data.yml && \
    echo "ROOT_DIR: $ROOT_DIR" >> data.yml && \
    echo "---" >> data.yml

RUN mustache data.yml nginx/nlp-web-app.$SERVER_TYPE.mustache > nginx/nlp-web-app && \
    rm -f nginx/nlp-web-app.$SERVER_TYPE.mustache && \
    ln -s /etc/nginx/sites-available/nlp-web-app /etc/nginx/sites-enabled/ && \
    rm -f /etc/nginx/sites-enabled/default

ADD docker_run.sh $ROOT_DIR/

ADD src/ $ROOT_DIR/src
RUN npm run prod

CMD ["./docker_run.sh"]
