#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

# based on
# https://www.digitalocean.com/community/tutorials/how-to-create-a-self-signed-ssl-certificate-for-nginx-in-ubuntu-18-04

set -x

# 5 years
DAYS="1825"

openssl req -x509 -nodes -days ${DAYS} \
        -newkey rsa:2048 -keyout nginx/certs/server.key \
        -out nginx/certs/server.crt \
        -subj '/C=US/ST=Maryland/L=Laurel/O=JHU\/APL/OU=PMAP\/NLP/CN=pmap-nlp'

openssl dhparam -out nginx/certs/dhparam.pem 4096
