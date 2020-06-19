#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# **********************************************************************
# Copyright (C) 2018 Johns Hopkins University Applied Physics Laboratory
#
# All Rights Reserved.
# This material may only be used, modified, or reproduced by or for the
# U.S. government pursuant to the license rights granted under FAR
# clause 52.227-14 or DFARS clauses 252.227-7013/7014.
# For any other permission, please contact the Legal Office at JHU/APL.
# **********************************************************************
import json
import logging.config
import os
import sys

import backoff
import time

def backoff_hdlr(details):
    print ("Backing off {wait:0.1f} seconds afters {tries} tries "
           "calling function {target} with args {args} and kwargs "
           "{kwargs}".format(**details))
    sys.stdout.flush()

def setup_logging():
    if "PINE_LOGGING_CONFIG_FILE" in os.environ and os.path.isfile(os.environ["PINE_LOGGING_CONFIG_FILE"]):
        with open(os.environ["PINE_LOGGING_CONFIG_FILE"], "r") as f:
            logging.config.dictConfig(json.load(f))
        logging.getLogger(__name__).info("Set logging configuration from file {}".format(os.environ["PINE_LOGGING_CONFIG_FILE"]))

# ----------------------------------------------------------------------
# Setup Redis Listeners
# ----------------------------------------------------------------------
@backoff.on_exception(backoff.expo, Exception, max_tries=10, on_backoff=backoff_hdlr)
def run():
    setup_logging()
    
    from .service_listener import ServiceListener, ServiceRegistration
    from ...shared.config import ConfigBuilder
    
    config = ConfigBuilder.get_config()
    logger = logging.getLogger(__name__)
    logger.info("Using ROOT_DIR={} MODELS_DIR={}".format(config.ROOT_DIR, config.MODELS_DIR))

    services = []
    for serv_obj in config.SERVICE_LIST:
        service = ServiceRegistration.from_registration_format(**serv_obj)
        if service.name in config.PIPELINE:
            logger.info("Enabling the following service: %s", service.to_registration_format())
            services.append(service)

    sl = ServiceListener(services=services)

    try:
        sl.start_workers()
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        sl.stop_workers()
        sys.exit(0)
    except Exception:
        raise
    finally:
        sl.stop_workers()
