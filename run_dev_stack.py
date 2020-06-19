#!/usr/bin/env python3
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import os
import select
import shlex
import signal
import subprocess
import sys
import threading
import time

DIR = os.path.dirname(os.path.realpath(__file__))

EVE_PORT = 5001
REDIS_PORT = 6379

PRINT_LOCK = threading.Lock()

LOCAL_DATA_DIR = os.path.join(DIR, "local_data", "dev")

def lock_print(message):
    PRINT_LOCK.acquire()
    try:
        print(message)
    finally:
        PRINT_LOCK.release()

def prepend_print(popen, prepend):
    def thread_run():
        while True:
            reads = [popen.stdout.fileno(), popen.stderr.fileno()]
            ret = select.select(reads, [], [])

            for fd in ret[0]:
                if fd == popen.stdout.fileno():
                    line = popen.stdout.readline()
                    if line != None and line.strip():
                        PRINT_LOCK.acquire()
                        try:
                            sys.stdout.buffer.write(prepend + line)
                            if not line.endswith(b"\n") and not line.endswith(b"\r"):
                                sys.stdout.buffer.write(b"\n")
                            sys.stdout.flush()
                        finally:
                            PRINT_LOCK.release()
                if fd == popen.stderr.fileno():
                    line = popen.stderr.readline()
                    if line != None and line.strip():
                        PRINT_LOCK.acquire()
                        try:
                            sys.stderr.buffer.write(prepend + line)
                            if not line.endswith(b"\n") and not line.endswith(b"\r"):
                                sys.stderr.buffer.write(b"\n")
                            sys.stderr.flush()
                        finally:
                            PRINT_LOCK.release()

            if popen.poll() != None:
                break

    thread = threading.Thread(target=thread_run)
    thread.start()
    return thread

def source_env_file():
    proc = subprocess.Popen(shlex.split("env -i bash -c 'set -a && source {}/.env && env'".format(DIR)), stdout = subprocess.PIPE)
    read_vars = {}
    for line in proc.stdout:
        (key, _, value) = line.decode().rstrip().partition("=")
        if key not in ["PWD", "SHLVL", "_"]:
            if not key in os.environ: # allow overriding
                os.environ[key] = value
                read_vars[key] = value
    proc.communicate()
    return read_vars

def start_eve_process(start_dir, start_cmd):
    lock_print("Starting eve process.")
    env = os.environ.copy()
    env["FLASK_PORT"] = str(EVE_PORT)
    env["DATA_DIR"] = os.path.join(LOCAL_DATA_DIR, "eve")
    env["LOG_DIR"] = env["DATA_DIR"]
    p = subprocess.Popen(start_cmd, env = env, cwd = start_dir, preexec_fn = os.setsid,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    t = prepend_print(p, b"\033[96m       eve:\033[00m ")
    return (p, t)

def stop_eve_process(p):
    lock_print("Stopping eve process.")
    os.killpg(os.getpgid(p[0].pid), signal.SIGTERM)
    p[1].join()

def start_redis_process(start_dir, start_cmd):
    lock_print("Starting redis process.")
    env = os.environ.copy()
    env["REDIS_PORT"] = str(REDIS_PORT)
    env["DATA_DIR"] = os.path.join(LOCAL_DATA_DIR, "redis")
    env["LOG_DIR"] = env["DATA_DIR"]
    p = subprocess.Popen(start_cmd, env = env, cwd = start_dir, preexec_fn = os.setsid,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    t = prepend_print(p, b"\033[92m     redis:\033[00m ")
    return (p, t)

def stop_redis_process(p):
    lock_print("Stopping redis process.")
    os.killpg(os.getpgid(p[0].pid), signal.SIGTERM)
    p[1].join()

def start_backend_process(start_dir, start_cmd):
    lock_print("Starting backend process.")
    env = os.environ.copy()
    env["EVE_SERVER"] = "http://localhost:{}".format(EVE_PORT)
    env["REDIS_SERVER"] = "localhost"
    env["REDIS_PORT"] = str(REDIS_PORT)
    env["DOCUMENT_IMAGE_DIR"] = os.path.join(LOCAL_DATA_DIR, "test_images")
    p = subprocess.Popen(start_cmd, env = env, cwd = start_dir, preexec_fn = os.setsid,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    t = prepend_print(p, b"\033[91m   backend:\033[00m ")
    return (p, t)

def stop_backend_process(p):
    lock_print("Stopping backend process.")
    os.killpg(os.getpgid(p[0].pid), signal.SIGTERM)
    p[1].join()

def start_frontend_annotation_process(start_dir, start_cmd):
    lock_print("Starting frontend annotation process.")
    p = subprocess.Popen(start_cmd, cwd = start_dir, preexec_fn = os.setsid,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    t = prepend_print(p, b"\033[95m  frontend:\033[00m ")
    return (p, t)

def stop_frontend_annotation_process(p):
    lock_print("Stopping frontend process.")
    os.killpg(os.getpgid(p[0].pid), signal.SIGTERM)
    p[1].join()

def start_pipeline(start_dir, start_cmd):
    lock_print("Starting pipeline process.")
    env = os.environ.copy()
    env["DATA_DIR"] = os.path.join(LOCAL_DATA_DIR, "pipelines")
    p = subprocess.Popen(start_cmd, env = env, cwd = start_dir, preexec_fn = os.setsid,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    t = prepend_print(p, b"\033[93m pipelines:\033[00m ")
    return (p, t)

def stop_pipeline(p):
    lock_print("Stopping pipeline process.")
    os.killpg(os.getpgid(p[0].pid), signal.SIGTERM)
    p[1].join()

def main():
    if not os.path.isdir(LOCAL_DATA_DIR):
        os.makedirs(LOCAL_DATA_DIR)
    
    os.environ["PINE_LOGGING_CONFIG_FILE"] = os.path.join(DIR, "shared", "logging.python.dev.json")
    e = source_env_file()
    if "VEGAS_CLIENT_SECRET" not in e:
        lock_print("Please set VEGAS_CLIENT_SECRET in .env.")
        return 1
    
    eve_dir = os.path.join(DIR, "eve")
    eve_start = os.path.join(eve_dir, "dev_run.sh")
    if not os.path.isfile(eve_start):
        lock_print("Couldn't find eve start script: {}.".format(eve_start))
        return 1
    
    redis_dir = os.path.join(DIR, "redis")
    redis_start = os.path.join(redis_dir, "dev_run.sh")
    if not os.path.isfile(redis_start):
        lock_print("Couldn't find redis start script: {}.".format(redis_start))
        return 1
    
    backend_dir = os.path.join(DIR, "backend")
    backend_start = os.path.join(backend_dir, "dev_run.sh")
    if not os.path.isfile(backend_start):
        lock_print("Couldn't find backend start script: {}.".format(backend_start))
        return 1
    
    frontend_annotation_dir = os.path.join(DIR, "frontend", "annotation")
    frontend_annotation_start = os.path.join(frontend_annotation_dir, "dev_run.sh")
    if not os.path.isfile(frontend_annotation_start):
        lock_print("Couldn't find frontend start script: {}/".format(frontend_annotation_start))
        return 1

    pipeline_dir = os.path.join(DIR, "pipelines")
    pipeline_start = os.path.join(pipeline_dir, "dev_run.sh")

    eve_process = start_eve_process(eve_dir, eve_start)
    redis_process = start_redis_process(redis_dir, redis_start)
    backend_process = start_backend_process(backend_dir, backend_start)
    frontend_annotation_process = start_frontend_annotation_process(frontend_annotation_dir, frontend_annotation_start)
    pipeline_process = start_pipeline(pipeline_dir, pipeline_start)

    def signal_handler(sig, frame):
        lock_print("")
        stop_pipeline(pipeline_process)
        stop_frontend_annotation_process(frontend_annotation_process)
        stop_backend_process(backend_process)
        stop_redis_process(redis_process)
        stop_eve_process(eve_process)
        lock_print("")
    
    signal.signal(signal.SIGINT, signal_handler)
    lock_print("Hit ctrl-c to exit.")
    signal.pause()

    return 0

if __name__ == "__main__":
    sys.exit(main())
