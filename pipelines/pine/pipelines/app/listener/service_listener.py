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
import traceback
import typing
import uuid
from datetime import timedelta

import pebble
import pydash
import redis
import time
from pebble import concurrent, ProcessPool

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
    results_queue_key = config.REDIS_PREFIX + config.PIPELINE + ":work-results"
    results_queue_key_timeout = timedelta(seconds=config.SERVICE_HANDLER_TIMEOUT * 2)
    running_jobs_key = config.REDIS_PREFIX + config.PIPELINE + ":running-jobs"
    classifiers_training_key = config.REDIS_PREFIX + config.PIPELINE + ":classifiers-training"

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
    def do_with_redis(callback: typing.Callable[[redis.StrictRedis], typing.Any]):
        local_redis = redis.StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT, charset="utf-8", decode_responses=True)
        time_to_spend_trying_to_acquire_lock = max(1, ServiceListener.processing_lock_key_timeout.total_seconds() // 2)
        max_retries = 10
        retry = 0
        last_exception = None
        while retry < max_retries:
            try:
                with local_redis.lock(ServiceListener.processing_lock_key,
                                      timeout=ServiceListener.processing_lock_key_timeout.total_seconds(),
                                      blocking_timeout=time_to_spend_trying_to_acquire_lock):
                    return callback(local_redis)
            except redis.exceptions.LockError as e:
                logger.exception("Unable to acquire lock in time")
                retry += 1
                last_exception = e
        # if we're here, we maxed out the retries
        logger.error("Maxed out %s retries trying to connect to redis", max_retries)
        raise last_exception

    @staticmethod
    def push_results(job_id: str, response):
        def callback(local_redis: redis.StrictRedis) -> None:
            response_key = ServiceListener.results_queue_key + ":" + job_id
            logger.info("Writing status to %s", response_key)
            local_redis.rpush(response_key, json.dumps(response, separators=(",", ":")))
            local_redis.expire(response_key, ServiceListener.results_queue_key_timeout)
        ServiceListener.do_with_redis(callback)

    @staticmethod
    def wait_until_classifier_isnt_training(classifier_id: str, job_id: str):
        def callback(local_redis: redis.StrictRedis) -> bool:
            return local_redis.hexists(ServiceListener.classifiers_training_key, classifier_id)
        while ServiceListener.do_with_redis(callback):
            logger.info("classifier %s is already running a training job, sleeping 10 seconds", classifier_id)
            time.sleep(10)
        def callback_set(local_redis: redis.StrictRedis) -> None:
            local_redis.hset(ServiceListener.classifiers_training_key, classifier_id, job_id)
        ServiceListener.do_with_redis(callback_set)

    @staticmethod
    def classifier_is_done_training(classifier_id: str):
        def callback(local_redis: redis.StrictRedis):
            return local_redis.hdel(ServiceListener.classifiers_training_key, classifier_id)
        return ServiceListener.do_with_redis(callback)

    @staticmethod
    def process_message(job_id: str, job_details):
        logger.info("process_message starting for job %s", job_id)
        
        job_type = pydash.get(job_details, "type", None)
        job_framework = pydash.get(job_details, "framework", None)
        classifier_id = pydash.get(job_details, "classifier_id", None)
        model_name = pydash.get(job_details, "model_name", None)

        try:
            if job_type == "fit":
                if not classifier_id:
                    raise ValueError("Need classifier_id to train")
                ServiceListener.wait_until_classifier_isnt_training(classifier_id, job_id)
                try:
                    logger.info("fit %s running", job_id)
                    pipeline = ner_api()
                    pipeline.train_model(model_name, classifier_id, job_framework)
                    logger.info("fit %s finished", job_id)
                finally:
                    ServiceListener.classifier_is_done_training(classifier_id)
            
            elif job_type == "predict":
                logger.info("predict %s running", job_id)
                document_ids = pydash.get(job_details, "document_ids", [])
                texts = pydash.get(job_details, "texts", [])
                pipeline = ner_api()
                try:
                    results = pipeline.predict(classifier_id, job_framework, document_ids, texts)
                    ServiceListener.push_results(job_id, results)
                except Exception as e:
                    results = {
                        "error": str(e)
                    }
                    ServiceListener.push_results(job_id, results)
                    raise e
                finally:
                    logger.info("predict %s finished", job_id)
            
            elif job_type == "status":
                logger.info("status %s running", job_id)
                pipeline = ner_api()
                status = pipeline.status(classifier_id, job_framework)
                logger.info("Received status from job_framework=%s classifier_id=%s: %s",
                            job_framework, classifier_id, status)
                ServiceListener.push_results(job_id, status)
                logger.info("status %s finished", job_id)
            
            else:
                logger.error("Service type, %s, unavailable", job_type)
                
        except Exception as e:
            logger.exception("Exception processing %s job", job_type)
            raise e

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
        with ProcessPool(max_workers=config.REDIS_MAX_PROCESSES) as pool:
            self.r_conn.delete(self.running_jobs_key) # clear out running jobs since this is a new startup
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
                if "job_id" not in job_details:
                    job_details["job_id"] = str(uuid.uuid4())
                job_id = pydash.get(job_details, "job_id")
                try:
                    logger.info("Received job id/details: %s/%s", job_id, job_details)
                    self.r_conn.sadd(self.running_jobs_key, job_id)
                    future = pool.schedule(ServiceListener.process_message, args=(job_id, job_details))
                    logger.debug("Got future for %s: %s", job_id, future)
                    def finished(f):
                        logger.info("Job %s has finished; removing from running jobs list", job_id)
                        self.r_conn.srem(self.running_jobs_key, job_id)
                    future.add_done_callback(finished)
                except Exception:
                    logger.exception("Exception processing message")
                    
                self.queue_processor_exit_event.wait(self.processor_poll.seconds)
