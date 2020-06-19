#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# **********************************************************************
# Copyright (C) 2019 Johns Hopkins University Applied Physics Laboratory
#
# All Rights Reserved.
# This material may only be used, modified, or reproduced by or for the
# U.S. government pursuant to the license rights granted under FAR
# clause 52.227-14 or DFARS clauses 252.227-7013/7014.
# For any other permission, please contact the Legal Office at JHU/APL.
# **********************************************************************
import asyncio
import atexit
import concurrent
import json
import logging
import os
import platform
import secrets
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Thread

import aioredis
import pydash
import redis
from pebble import ThreadPool

from ..shared.config import ConfigBuilder

config = ConfigBuilder.get_config()
logger = logging.getLogger(__name__)


class ServiceManager(object):
    # Redis Client
    logger.info("Using redis host {}:{}".format(config.REDIS_HOST, config.REDIS_PORT))
    r_pool = redis.ConnectionPool(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
    r_conn = redis.StrictRedis(connection_pool=r_pool, charset="utf-8", decode_responses=True)

    # Redis Key Prefixes
    redis_key_prefix = config.REDIS_PREFIX + "registration:"
    redis_reg_key_prefix = redis_key_prefix + "codex:"
    redis_channels_key = redis_key_prefix + "channels"
    redis_channel_ttl_key_prefix = redis_key_prefix + "channel-ttl:"  # not really ttl, but more like registered date
    redis_work_queue_key_prefix = redis_key_prefix + "work-queue:"
    redis_work_mutex_key_prefix = redis_key_prefix + "work-mutex:"
    redis_handler_mutex_key_prefix = redis_key_prefix + "handler-mutex:"

    # Redis Key TTL (Used by Expire Calls)

    # this is how long a registered-service will live unless it get's an update
    redis_reg_key_ttl = int(timedelta(seconds=config.SCHEDULER_REGISTRATION_TIMEOUT).total_seconds())
    redis_channels_key_ttl = int(timedelta(minutes=60).total_seconds())  # do not touch (this is how long the overall list of channels will live)
    redis_work_queue_key_ttl = int(timedelta(seconds=config.SCHEDULER_QUEUE_TIMEOUT).total_seconds())  # how long a job can sit in the queue before it expires

    # Redis Mutex Key TTL (Use by locks)
    redis_work_mutex_key_ttl = int(timedelta(minutes=10).total_seconds())  # how long can this mutex be acquired
    redis_handler_mutex_key_ttl = int(timedelta(seconds=5).total_seconds())  # how long should the same handler for the same job be locked from running...

    # Timeouts
    # how long a handler should take (may not kill it in all platforms if expired because it's a thread)
    handler_timeout = int(timedelta(seconds=config.SCHEDULER_HANDLER_TIMEOUT).total_seconds())

    # Worker Names
    registration_worker_name = "registration_worker"
    processing_worker_name = "processing_worker"
    channel_worker_name = "channel_worker"

    # Channel Names
    shutdown_channel = "shutdown"
    registration_channel = "registration"

    # Reserved Channels
    reserved_channels = frozenset({shutdown_channel, registration_channel})

    def __init__(self, default_handler=None):
        """
        :type default_handler: callable
        """
        self.shutdown_key = secrets.token_hex(16)  # 32-char thread-local shutdown secret (prevents external service from shutting down listeners)
        self.aio_loop = asyncio.new_event_loop()  # this event loop is mean to use in non-main thread
        self.registered_channels = set()  # type: set[str]
        self.is_running = False  # flag to use to quickly determine if system has started
        self.pubsubs = dict()  # type: dict[str, redis.client.PubSub] # keep's all the thread-local pubsubs
        self.workers = dict()  # type: dict[str, Thread] # keep's all the worker threads
        self.handlers = dict()  # type: dict[str, callable] # handler dictionary for future dynamic hanlders
        self.handlers["default"] = default_handler if callable(default_handler) else lambda: None  # register default handler
        # make sure things are stopped properly
        atexit.register(self.stop_listeners)

    @classmethod
    def get_registered_channels(cls, include_ttl=False):
        """
        Get list of registered channels, with registration time if requested.
        :type include_ttl: bool
        :rtype: list[str] | dict[str, datetime]
        """
        registered_channels = cls.r_conn.smembers(cls.redis_channels_key)
        if not include_ttl:
            return list(registered_channels)
        with cls.r_conn.pipeline() as pipe:
            for channel in registered_channels:
                pipe.get(cls.redis_channel_ttl_key_prefix + channel)
            values = pipe.execute()
        final_values = []
        for redis_val in values:
            try:
                channel_ttl_int = pydash.parse_int(redis_val, 10)
                redis_val = datetime.utcfromtimestamp(channel_ttl_int)
            except (ValueError, TypeError):
                continue
            final_values.append(redis_val)
        return dict(zip(registered_channels, final_values))

    @classmethod
    def get_registered_service_details(cls, service_name=None):
        """
        Get registration details of a service.
        :type service_name: str
        :rtype: None | dict
        """
        if not isinstance(service_name, str):
            return None
        service_details = cls.r_conn.get(cls.redis_reg_key_prefix + service_name)
        try:
            service_details = json.loads(service_details)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Unable to decode service details")
            return None
        return service_details

    @classmethod
    def get_registered_services(cls, include_details=True):
        """
        Get list of registered services and registration body if requested.
        :type include_details: bool
        :rtype: list[str] | list[dict]
        """
        registered_keys = []
        registered_names = []
        for key in cls.r_conn.scan_iter(match=cls.redis_reg_key_prefix + "*"):
            service_name = key.rsplit(":", 1)[-1]  # "<prefix>:registration:codex:<name>" --> [<prefix>:registration, <name>]
            registered_names.append(service_name)
            registered_keys.append(key)
        if not include_details:
            return registered_names
        with cls.r_conn.pipeline() as pipe:
            for key in registered_keys:
                pipe.get(key)
            values = pipe.execute()
        final_values = []
        for redis_val in values:
            try:
                final_values.append(json.loads(redis_val))
            except (json.JSONDecodeError, TypeError):
                continue
        return final_values

    @classmethod
    def send_service_request(cls, service_name, data, job_id=None, encoder=None):
        """
        Queue's a job for the requested service.
        :type service_name: str
        :type data: dict
        :type job_id: str
        :type encoder: json.JSONEncoder
        :rtype: None | dict
        """
        registered_services = cls.get_registered_services(include_details=False)
        if service_name not in set(registered_services):
            logger.warning("Unable to retrieve service.")
            return None
        service_details = cls.r_conn.get(cls.redis_reg_key_prefix + service_name)
        if not service_details:
            logger.warning("Unable to retrieve service details.")
            return None
        try:
            service_details = json.loads(service_details)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Unable to load service details.")
            return None
        service_channel = pydash.get(service_details, "channel", None)
        if not isinstance(service_channel, str):
            logger.warning("Unable to load service details.")
            return None
        redis_queue_key = cls.redis_work_queue_key_prefix + service_name
        job_id_to_use = job_id if isinstance(job_id, str) else uuid.uuid4().hex
        request_body = {"job_id": job_id_to_use, "job_type": "request", "job_queue": redis_queue_key}
        request_body_publish = json.dumps(request_body.copy(), separators=(",", ":"), cls=encoder)
        request_body.update({"job_data": data})
        try:
            request_body_queue = json.dumps(request_body, separators=(",", ":"), cls=encoder)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Unable to encode data.")
            return None
        with cls.r_conn.pipeline() as pipe:
            pipe.rpush(redis_queue_key, request_body_queue)
            # if nothing is processed in "redis_queue_key_ttl" minutes since last insert, the queue will be deleted
            pipe.expire(redis_queue_key, cls.redis_work_queue_key_ttl)
            num_pushed, expire_is_set = pipe.execute()
        if num_pushed < 1 or expire_is_set is not True:
            return None
        num_received = cls.r_conn.publish(service_channel, request_body_publish)
        # no-one consumed it
        if num_received <= 0:
            # TODO: potential race-condition here due to popping potentially wrong thing in multi-process (we should use a lock)
            cls.r_conn.rpop(redis_queue_key)
            return None
        return request_body

    def start_listeners(self):
        """
        Starts all the workers.
        """
        if not self.is_running:
            reg_started = self._start_registration_listener()
            proc_started = self._start_processing_listeners()
            self.is_running = reg_started and proc_started

    def stop_listeners(self):
        """
        Stops all the workers.
        """
        self.r_conn.publish(self.shutdown_channel, "exit_%s" % self.shutdown_key)
        self.aio_loop.call_soon_threadsafe(self._stop_channel_watchdog)
        for t_id, thread in self.workers.items():
            if isinstance(thread, Thread):
                thread.join()
        self.is_running = False

    def _start_registration_listener(self):
        """
        Starts the registration worker.
        :rtype: bool
        """
        if self.registration_worker_name in self.workers:
            return
        worker = Thread(target=self._registration_listener)
        worker.setDaemon(True)  # Make sure it exits when main program exits
        worker.setName("NLP Redis Registration Listener")
        worker.start()  # Start the thread
        self.workers[self.registration_worker_name] = worker
        logger.debug("registration worker started")
        return worker.is_alive()

    def _start_processing_listeners(self):
        """
        Starts the processing workers.
        :rtype: bool
        """
        if self.processing_worker_name in self.workers:
            return
        worker = Thread(target=self._processing_listener)
        aio_worker = Thread(target=self._start_channel_watchdog)
        worker.setDaemon(True)  # Make sure it exits when main program exits
        aio_worker.setDaemon(True)
        worker.setName("NLP Redis Processing Listener")
        aio_worker.setName("NLP Redis Channel Listener")
        worker.start()  # Start the thread
        aio_worker.start()
        self.workers[self.processing_worker_name] = worker
        self.workers[self.channel_worker_name] = aio_worker
        return worker.is_alive() and aio_worker.is_alive()

    def _start_channel_watchdog(self):
        """
        Starts the channel watchdog workers in an asyncio-only thread. It monitors the channel TTL's.
        :rtype: bool
        """
        asyncio.set_event_loop(self.aio_loop)
        try:
            self.aio_loop.run_until_complete(self._channel_watchdog())
        except asyncio.CancelledError:
            pass

    def _stop_channel_watchdog(self):
        """
        Stops the channel watchdog workers in an asyncio-only thread.
        :rtype: bool
        """
        asyncio.set_event_loop(self.aio_loop)
        tasks = list(asyncio.Task.all_tasks(self.aio_loop))  # type: ignore
        tasks_to_cancel = {t for t in tasks if not t.done()}
        for task in tasks_to_cancel:  # type: asyncio.Task
            task.cancel()

    def _registration_listener(self):
        """
        Registration Listener Implementation.
        """
        logger.debug("Starting Registration Listener")
        pubsub = self.r_conn.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(self.registration_channel, self.shutdown_channel)
        self.pubsubs[self.registration_worker_name] = pubsub
        for msg in pubsub.listen():
            valid_shutdown_channel = "channel" in msg and "data" in msg and msg["channel"] == self.shutdown_channel
            valid_register_channel = "channel" in msg and "data" in msg and msg["channel"] == self.registration_channel
            # Skip message if invalid channel (shouldn't happen)
            if not (valid_register_channel or valid_shutdown_channel):
                continue
            # Exit if shutdown message is received... (with private key)
            if valid_shutdown_channel:
                if msg["data"] == "exit_%s" % self.shutdown_key:
                    logger.debug("Exiting Registration Listener")
                    return
                else:
                    continue
            # Parse Message...
            try:
                registration_body = json.loads(msg["data"])
            except (json.JSONDecodeError, TypeError) as e:
                logger.error("Invalid Registration Message Format")
                continue
            # Extract Message Details
            name = pydash.get(registration_body, "name", None)
            version = pydash.get(registration_body, "version", None)
            channel = pydash.get(registration_body, "channel", None)
            framework = pydash.get(registration_body, "service.framework", None)
            framework_types = pydash.get(registration_body, "service.types", None)
            # Validate Message Types
            var_list = (name, version, channel, framework, framework_types,)
            type_list = (str, str, str, str, list,)
            type_check = (type(val) == type_list[idx] for idx, val in enumerate(var_list))
            if not all(type_check):
                logger.warning("Invalid Registration Body Format %s %s %s %s %s", name, version, channel, framework, framework_types)
                continue
            types_validation = (isinstance(val, str) for val in framework_types)
            if not all(types_validation):
                logger.warning("Invalid Registration Body Types")
                continue
            # Verify that the channel in the registration data is not reserved... (to prevent hijacking of a channel)
            if channel in self.reserved_channels:
                logger.warning("Channel Name %s is reserved.", channel)
                continue
            # redis key to track registration information
            redis_reg_data = dict(name=name, version=version, channel=channel, framework=framework, framework_types=framework_types)
            redis_reg_data_str = json.dumps(redis_reg_data, separators=(",", ":"))
            redis_reg_key = self.redis_reg_key_prefix + name  # e.g. prefix:registration:codex:name
            redis_reg_key_ttl = self.redis_reg_key_ttl
            # redis key to track all registered channels
            redis_channels_key = self.redis_channels_key
            redis_channels_key_ttl = self.redis_channels_key_ttl
            # redis key to track channel expiration from list of registered channels
            redis_channel_ttl_track_key = self.redis_channel_ttl_key_prefix + channel
            try:
                # Schema after this
                # "<prefix>:registration:channels" --> SET of all channels
                # "<prefix>:registration:channel-ttl:<channel_name>" <-- holds the dates the channels were added (to be able to remove them if expired)
                # "<prefix>:registration:codex:<service_name>" <-- holds registration info
                with self.r_conn.pipeline() as pipe:
                    # nothing wrong with setting the same key more than once, it's the TTL that matters...
                    pipe.setex(redis_reg_key, redis_reg_key_ttl, redis_reg_data_str)
                    pipe.sadd(redis_channels_key, channel)
                    pipe.expire(redis_channels_key, redis_channels_key_ttl)
                    pipe.setex(redis_channel_ttl_track_key, redis_reg_key_ttl, int(time.time()))
                    pipe.execute()
                    self.registered_channels.add(channel)
            except redis.RedisError as e:
                logger.warning("Unable to register channel.")
                continue

    async def _channel_watchdog(self):
        """
        Channel Watchdog Implementation.
        In asyncio, it monitors the channel-ttl keys and the channels SET to expire registered services as needed.
        The other functionality is to register new channels as they're added to the pubsub in the processing listener.
        """
        redis_aio_pool = None
        try:
            logger.debug("Starting Channel Watchdog")
            redis_aio_pool = await aioredis.create_redis_pool(address=(config.REDIS_HOST, config.REDIS_PORT,),
                                                              db=config.REDIS_DBNUM,
                                                              encoding="UTF-8",
                                                              loop=self.aio_loop)
            redis_reg_key_ttl_timedelta = timedelta(seconds=self.redis_reg_key_ttl)
            while True:
                # get list of channels
                channels = await redis_aio_pool.smembers(self.redis_channels_key)
                # for each channel, verify when it was added
                for channel in channels:
                    channel_ttl = await redis_aio_pool.get(self.redis_channel_ttl_key_prefix + channel)
                    if not isinstance(channel_ttl, str):
                        continue
                    # parse dates
                    try:
                        channel_ttl_int = pydash.parse_int(channel_ttl, 10)
                        channel_ttl_date = datetime.utcfromtimestamp(channel_ttl_int)
                    except (ValueError, TypeError):
                        continue
                    # if expired, remove!
                    if channel_ttl_date + redis_reg_key_ttl_timedelta < datetime.utcnow():
                        self.registered_channels.remove(channel)
                        await redis_aio_pool.srem(self.redis_channels_key, channel)
                # verify list of channels again
                channels = await redis_aio_pool.smembers(self.redis_channels_key)
                # add any remaining channels to the channels-to-be-monitored
                self.registered_channels.update(channels)
                has_valid_pubsub = self.processing_worker_name in self.pubsubs and isinstance(self.pubsubs[self.processing_worker_name], redis.client.PubSub)
                if has_valid_pubsub and len(channels) > 0:
                    # this is fine because of the python's GIL...
                    self.pubsubs[self.processing_worker_name].subscribe(*channels)
                await asyncio.sleep(1)  # being nice
        except asyncio.CancelledError as e:
            logger.debug("Terminating Channel Watchdog")
            raise  # re-raise is needed to safely terminate
        except aioredis.errors.RedisError:
            logger.error("Redis Error on Channel Watchdog")
        finally:
            if redis_aio_pool:
                redis_aio_pool.close()
                await redis_aio_pool.wait_closed()

    @staticmethod
    def _thread_killer(thread_id):
        # Inspired by http://tomerfiliba.com/recipes/Thread2/
        # Only works on Cpython distribution of python as it uses the pthread api directly...
        # Will also not work if the thread doesn't acquire the GIL again (e.g. it's stuck in a System Call... like open)
        if platform.python_implementation() != "CPython":
            logger.critical("Unable to kill thread due to platform implementation. Memory Leak may occur...")
            return False
        import ctypes
        thread_id = ctypes.c_long(thread_id)
        exception = ctypes.py_object(SystemExit)
        set_count = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, exception)
        if set_count == 0:
            logger.critical("Failed to set exception in thread %s. Invalid Thread ID. Memory Leak may occur...", thread_id.value)
            return False
        elif set_count > 1:
            logger.critical("Exception was set in multiple threads with id %s. Trying to undo. Memory Leak may occur...", thread_id.value)
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, ctypes.c_long(0))
            return False
        return True

    def _processing_listener_handler_wrapper(self, job_id, job_type, job_queue, job_data):

        with self.r_conn.lock(self.redis_work_mutex_key_prefix + job_id, timeout=self.redis_work_mutex_key_ttl):
            has_handler_lock = self.r_conn.exists(self.redis_handler_mutex_key_prefix + job_id)
            if not has_handler_lock:
                self.r_conn.setex(self.redis_handler_mutex_key_prefix + job_id, self.redis_handler_mutex_key_ttl, job_id)
            else:
                return

        service_name = job_queue.rsplit(":", 1)[-1]  # "<prefix>:registration:codex:<name>" --> [<prefix>:registration, <name>]
        job_info = self.get_registered_service_details(service_name)  # job registration info
        if not job_info:
            self.r_conn.delete(self.redis_handler_mutex_key_prefix + job_id)
            return

        logger.debug("Received new job to process with id %s by process %s", job_id, os.getpid())
        with ThreadPool(max_workers=1) as executor:
            future = executor.schedule(self.handlers["default"], args=(job_id, job_type, job_info, job_data))
            try:
                future.result(timeout=self.handler_timeout)
                logger.debug("Job with id %s finished by process %s", job_id, os.getpid())
            except concurrent.futures.TimeoutError:
                logger.warning("Timeout occurred in Job with id %s by process %s", job_id, os.getpid())
                for t in executor._pool_manager.workers:  # type: Thread
                    thread_id = t.ident
                    if t.is_alive():
                        logger.warning("Attempting to kill thread with id %s timeout occurred in process %s", thread_id, os.getpid())
                        is_killed = self._thread_killer(thread_id)
                        if is_killed:
                            logger.debug("Successfully killed thread with id %s in process %s", thread_id, os.getpid())
            finally:
                self.r_conn.delete(self.redis_handler_mutex_key_prefix + job_id)

    def _processing_listener(self):
        """
        Processing Listener Implementation.
        Runs a handler when a processing message gets send over an already registered channel.
        """
        logger.debug("Starting Processing Listener")
        pubsub = self.r_conn.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(self.shutdown_channel)
        self.pubsubs[self.processing_worker_name] = pubsub
        for msg in pubsub.listen():
            valid_shutdown_channel = "channel" in msg and "data" in msg and msg["channel"] == self.shutdown_channel
            valid_registered_channel = "channel" in msg and "data" in msg and msg["channel"] in self.registered_channels
            # this may happen since we're registering channels dynamically (in the watchdog)
            if not (valid_registered_channel or valid_shutdown_channel):
                continue
            # verify if this thread should exit
            if valid_shutdown_channel:
                if msg["data"] == "exit_%s" % self.shutdown_key:
                    logger.debug("Exiting Processing Listener")
                    return
                else:
                    continue
            # parse message
            try:
                channel_body = json.loads(msg["data"])
            except (json.JSONDecodeError, TypeError) as e:
                logger.error("Invalid Body Message Format")
                continue
            # get specific details about the message
            # it needs to have at least a job_id and a job_type (request, response)
            # TODO: create classes for these fields...
            job_id = pydash.get(channel_body, "job_id", None)
            job_type = pydash.get(channel_body, "job_type", None)
            job_queue = pydash.get(channel_body, "job_queue", None)
            job_data = pydash.get(channel_body, "job_data", None)
            # this side only handle's "response" types, the services handle the "request"
            is_valid_msg = isinstance(job_id, str) and job_type == "response" and isinstance(job_queue, str)
            if not is_valid_msg:
                continue
            # Process Job
            self._processing_listener_handler_wrapper(job_id, job_type, job_queue, job_data)


if __name__ == '__main__':
    sm = ServiceManager()
    sm.start_listeners()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sm.stop_listeners()
        pass
