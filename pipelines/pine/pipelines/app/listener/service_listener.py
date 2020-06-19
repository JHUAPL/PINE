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
import atexit
import json
import logging
import threading
from datetime import timedelta

import pebble
import pydash
import redis
import time
from pebble import concurrent

from ...shared.config import ConfigBuilder
from ...NER_API import ner_api

config = ConfigBuilder.get_config()
logger = logging.getLogger(__name__)


class ServiceRegistration(object):

    def __init__(self, name, version, channel, framework, framework_types):
        self.name = name
        self.version = version
        self.channel = channel
        self.framework = framework
        self.framework_types = framework_types

    @classmethod
    def from_registration_format(cls, **kwargs):
        name = kwargs.pop("name", None)
        version = kwargs.pop("version", None)
        channel = kwargs.pop("channel", None)
        service = kwargs.pop("service", {})
        framework = service.pop("framework", None) if isinstance(service, dict) else None
        framework_types = service.pop("types", None) if isinstance(service, dict) else None
        return cls(name, version, channel, framework, framework_types)

    def to_registration_format(self):
        return dict(
            name=self.name,
            version=self.version,
            channel=self.channel,
            service=dict(
                framework=self.framework,
                types=self.framework_types
            )
        )


class ServiceListener(object):
    # Redis Client
    r_pool = redis.ConnectionPool(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
    r_conn = redis.StrictRedis(connection_pool=r_pool, charset="utf-8", decode_responses=True)

    # Timeouts
    registration_poll = timedelta(seconds=config.SERVICE_REGISTRATION_FREQUENCY)  # re-register every x seconds
    listener_poll = timedelta(seconds=config.SERVICE_LISTENING_FREQUENCY)  # Listen to messages every x seconds
    processor_poll = timedelta(seconds=config.SERVICE_LISTENING_FREQUENCY)  # Listen to queue every x seconds
    processing_limit = timedelta(minutes=config.SERVICE_HANDLER_TIMEOUT)  # Timeout for processing a job...

    # Scheduled Keys
    processing_queue_key = config.REDIS_PREFIX + config.PIPELINE + "work-queue"
    processing_queue_key_timeout = timedelta(seconds=config.SERVICE_HANDLER_TIMEOUT * 2)  # Timeout for queueing processing a job...

    # Mutexes Keys
    processing_lock_key = config.REDIS_PREFIX + "locks:processing"
    processing_lock_key_timeout = timedelta(minutes=config.SERVICE_HANDLER_TIMEOUT)
    preprocessing_lock_key = config.REDIS_PREFIX + "locks:preprocessing"
    preprocessing_lock_key_timeout = int(timedelta(seconds=config.SERVICE_HANDLER_TIMEOUT).total_seconds())
    preprocessing_worker_lock_key = config.REDIS_PREFIX + "locks:preprocessing_worker"
    preprocessing_worker_lock_key_timeout = int(timedelta(seconds=config.SERVICE_HANDLER_TIMEOUT).total_seconds())

    # Channels
    registration_channel = config.SERVICE_REGISTRATION_CHANNEL or "registration"

    def __init__(self, services=None):
        """
        :type services: list[ServiceRegistration]
        """
        self.is_running = False
        self.registration_exit_event = threading.Event()
        self.channel_exit_event = threading.Event()
        self.listener_exit_event = threading.Event()
        self.queue_processor_exit_event = threading.Event()
        self.registration_thread = None
        self.channel_thread = None
        self.listener_thread = None
        self.queue_processor_thread = None
        self.r_pubsub = self.r_conn.pubsub(ignore_subscribe_messages=True)
        self.services = services if isinstance(services, list) else list()
        # make sure things are stopped properly
        atexit.register(self.stop_workers)

    @classmethod
    def publish_response(cls, channel, data):
        """
        :type channel: str
        :type data: dict
        :rtype: bool
        """
        pass

    def start_workers(self):
        is_registration_thread_alive = isinstance(self.registration_thread, threading.Thread) and self.registration_thread.is_alive()
        is_channel_thread_alive = isinstance(self.channel_thread, threading.Thread) and self.channel_thread.is_alive()
        is_listener_thread_alive = isinstance(self.listener_thread, threading.Thread) and self.listener_thread.is_alive()
        is_queue_processor_alive = isinstance(self.queue_processor_thread, threading.Thread) and self.queue_processor_thread.is_alive()
        if not is_registration_thread_alive:
            logger.info("Starting Registration Worker")
            # Clear Exit Event
            self.registration_exit_event.clear()
            # Start Registration Thread
            self.registration_thread = threading.Thread(target=self._start_registration_task, name="Active Learning Redis Registration Worker", daemon=True)
            self.registration_thread.start()
        if not is_channel_thread_alive:
            logger.info("Starting Channel Watchdog")
            # Clear Exit Event
            self.channel_exit_event.clear()
            # Start Channel Watchdog Thread
            self.channel_thread = threading.Thread(target=self._start_channel_task, name="Active Learning Redis Channel Worker", daemon=True)
            self.channel_thread.start()
        if not is_listener_thread_alive:
            logger.info("Starting Message Listener")
            # Clear Exit Event
            self.listener_exit_event.clear()
            # Start Listener Thread
            self.listener_thread = threading.Thread(target=self._start_listener_task, name="Active Learning Redis Listener Worker", daemon=True)
            self.listener_thread.start()
        if not is_queue_processor_alive:
            logger.info("Starting Queue Processor")
            # Clear Exit Event
            self.queue_processor_exit_event.clear()
            # Start Queue Processor Thread
            self.queue_processor_thread = threading.Thread(target=self._start_queue_processor_task, name="Active Learning Redis Queue Processor", daemon=True)
            self.queue_processor_thread.start()
        self.is_running = True

    def stop_workers(self):
        is_registration_thread_alive = isinstance(self.registration_thread, threading.Thread) and self.registration_thread.is_alive()
        is_channel_thread_alive = isinstance(self.channel_thread, threading.Thread) and self.channel_thread.is_alive()
        is_listener_thread_alive = isinstance(self.listener_thread, threading.Thread) and self.listener_thread.is_alive()
        is_queue_processor_alive = isinstance(self.queue_processor_thread, threading.Thread) and self.queue_processor_thread.is_alive()
        if is_registration_thread_alive:
            logger.info("Exiting Registration Worker")
            self.registration_exit_event.set()
            self.registration_thread.join()
        if is_channel_thread_alive:
            logger.info("Exiting Channel Watchdog")
            self.channel_exit_event.set()
            self.channel_thread.join()
        if is_listener_thread_alive:
            logger.info("Exiting Message Listener")
            self.listener_exit_event.set()
            self.listener_thread.join()
        if is_queue_processor_alive:
            logger.info("Exiting Queue Processor")
            self.queue_processor_exit_event.set()
            self.queue_processor_thread.join()
        # clear-out any redis-locks...
        if self.r_conn.exists(self.processing_lock_key):
            self.r_conn.delete(self.processing_lock_key)
        if self.r_conn.exists(self.preprocessing_lock_key):
            self.r_conn.delete(self.preprocessing_lock_key)
        self.is_running = False

    def pre_process_message(self, message_channel, message_data):
        """
        :type message_channel: str
        :type message_data: str | bytes
        :rtype: bool | dict
        """
        try:
            decoded_message = json.loads(message_data)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Invalid Processing Message")
            return False
        publish_job_id = pydash.get(decoded_message, "job_id", None)
        publish_job_type = pydash.get(decoded_message, "job_type", None)
        publish_job_queue = pydash.get(decoded_message, "job_queue", None)
        is_valid_msg = isinstance(publish_job_id, str) and publish_job_type == "request" and isinstance(publish_job_queue, str)
        if not is_valid_msg:
            logger.warning("Invalid Processing Message")
            return False

        with self.r_conn.lock(self.preprocessing_lock_key, timeout=self.preprocessing_lock_key_timeout):
            logger.info("Received new job to process with id %s", publish_job_id)
            queue_data = self.r_conn.lrange(publish_job_queue, 0, -1)
            idx_found = None
            for idx, data in enumerate(queue_data):
                try:
                    decoded_message = json.loads(data)
                    job_id = pydash.get(decoded_message, "job_id", None)
                    if job_id == publish_job_id:
                        idx_found = idx
                except (json.JSONDecodeError, TypeError):
                    continue
            if not isinstance(idx_found, int):
                logger.warning("Unable to find message in the Queue")
                return False
            self.r_conn.lset(publish_job_queue, idx_found, b"TO_BE_DELETED")
            self.r_conn.lrem(publish_job_queue, 1, b"TO_BE_DELETED")

        final_job_data = queue_data[idx_found]
        try:
            decoded_message = json.loads(final_job_data)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Invalid Processing Message in Queue")
            return False

        job_id = pydash.get(decoded_message, "job_id", None)
        job_data = pydash.get(decoded_message, "job_data", None)
        valid_queued_job = isinstance(job_id, str) and isinstance(job_data, dict) and job_id == publish_job_id
        if not valid_queued_job:
            logger.warning("Invalid Processing Message in Queue")
            return False
        logger.info("New Job received over channel %s", message_channel)
        job_data.update({"job_id": job_id, "job_channel": message_channel, "job_queue": publish_job_queue})  # making sure it has the proper Job ID
        return job_data

    @staticmethod
    @concurrent.process(timeout=processing_limit.seconds)
    def process_message(job_details):
        local_redis = redis.StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT, charset="utf-8", decode_responses=True)
        time_to_spend_trying_to_acquire_lock = max(1, ServiceListener.processing_lock_key_timeout.total_seconds() // 2)
        try:
            with local_redis.lock(ServiceListener.processing_lock_key,
                                  timeout=ServiceListener.processing_lock_key_timeout.total_seconds(),
                                  blocking_timeout=time_to_spend_trying_to_acquire_lock):
                job_type = pydash.get(job_details, "type", None)
                job_framework = pydash.get(job_details, "framework", None)
                classifier_id = pydash.get(job_details, "classifier_id", None)

                if job_type == "fit":
                    model_name = pydash.get(job_details, "model_name", None)
                    pipeline = ner_api()
                    try:
                        pipeline.train_model(model_name, classifier_id, job_framework)
                    except Exception as e:
                        logger.error("ERROR: Could not train classifier, error: {}".format(e))
                        # TODO: return status to the front end, either by adding a redis listener or setting job status
                        # as failed in the database
                    logger.info('fit completed')

                elif job_type == "predict":
                    pipeline = ner_api()
                    documents = pydash.get(job_details, "documents", [])
                    doc_ids = pydash.get(job_details, "doc_ids", [])
                    try:
                        results = pipeline.predict(classifier_id, job_framework, documents, doc_ids)
                    except Exception as e:
                        logger.error("ERROR: Could not predict document annotations, error: {}".format(e))
                        # TODO: return status, stating that were unable to execute a predict from the given parameters

                    # TODO: return results through redis

                else:
                    logger.error("Service type, {}, unavailable".format(job_type))
                    return
        except redis.exceptions.LockError as e:
            logger.info("Unable to acquire lock in time, re-scheduling job...")
            local_redis.rpush(ServiceListener.processing_queue_key, json.dumps(job_details, separators=(",", ":")))

    def _start_registration_task(self):
        while not self.registration_exit_event.is_set():
            for service in self.services:
                registration_msg = json.dumps(service.to_registration_format(), separators=(",", ":"))
                self.r_conn.publish(self.registration_channel, registration_msg)
            self.registration_exit_event.wait(self.registration_poll.seconds)

    def _start_channel_task(self):
        while not self.channel_exit_event.is_set():
            should_resubscribe = len(self.r_pubsub.channels) < len(self.services)
            if should_resubscribe:
                for service in self.services:
                    # Skip registration channel
                    if service.channel == self.registration_channel:
                        continue
                    if service.channel not in self.r_pubsub.channels:
                        self.r_pubsub.subscribe(service.channel)
            self.channel_exit_event.wait(self.listener_poll.seconds)

    def _start_listener_task(self):
        while not self.listener_exit_event.is_set():
            if not self.r_pubsub.subscribed:
                self.listener_exit_event.wait(self.listener_poll.seconds)
                continue
            msg = self.r_pubsub.get_message()
            valid_msg = msg and "type" in msg and "channel" in msg and "data" in msg
            if valid_msg and msg["type"] == "message":
                job_details = self.pre_process_message(msg["channel"], msg["data"])
                if job_details:
                    logger.info("Adding Job with ID %s to Service Queue", job_details["job_id"])
                    self.r_conn.rpush(self.processing_queue_key, json.dumps(job_details, separators=(",", ":")))
                    self.r_conn.expire(self.processing_queue_key, self.processing_queue_key_timeout)
            self.listener_exit_event.wait(self.listener_poll.seconds)

    def _start_queue_processor_task(self):
        while not self.queue_processor_exit_event.is_set():
            msg_in_queue = self.r_conn.lpop(self.processing_queue_key)
            if not msg_in_queue:
                self.queue_processor_exit_event.wait(self.processor_poll.seconds)
                continue
            try:
                job_details = json.loads(msg_in_queue)
            except (json.JSONDecodeError, TypeError):
                logger.warning("Invalid Job Details Message")
                continue
            # will allow one processor at a time (due to internal locking)
            self.process_message(job_details)  # type: pebble.ProcessFuture
            self.queue_processor_exit_event.wait(self.processor_poll.seconds)
