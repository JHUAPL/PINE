#!/usr/bin/env python3
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import enum
import os
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

class Color(enum.Enum):
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    LIGHT_RED = 91
    LIGHT_GREEN = 92
    LIGHT_YELLOW = 93
    LIGHT_BLUE = 94
    LIGHT_MAGENTA = 95
    LIGHT_CYAN = 96

def lock_print(message):
    PRINT_LOCK.acquire()
    try:
        print(message)
    finally:
        PRINT_LOCK.release()

def source_env_file():
    proc = subprocess.Popen(shlex.split("env -i bash -c 'set -a && source {}/.env && env'".format(DIR)), stdout=subprocess.PIPE)
    read_vars = {}
    for line in proc.stdout:
        (key, _, value) = line.decode().rstrip().partition("=")
        if key not in ["PWD", "SHLVL", "_"]:
            if not key in os.environ: # allow overriding
                os.environ[key] = value
                read_vars[key] = value
    proc.communicate()
    return read_vars

def prepend_cmd(cmd, prefix_text, prefix_color):
    p = ["{}/prepend.sh".format(DIR),
         b"\033[" + str(prefix_color).encode() + b"m" + prefix_text.encode() + b"\033[00m",
         b"\033[" + str(prefix_color).encode() + b"m" + prefix_text.encode() + b"[\033[" + str(Color.RED.value).encode() + b"merr\033[" + str(prefix_color).encode() + b"m]\033[00m"]
    if isinstance(cmd, list):
        p += cmd
    else:
        p.append(cmd)
    return p

def set_version():
    proc = subprocess.run([os.path.join(DIR, "version.sh")], shell=True, check=True, stdout=subprocess.PIPE)
    os.environ["PINE_VERSION"] = proc.stdout.strip().decode()

def start_eve_process(start_dir, start_cmd):
    lock_print("Starting eve process.")
    env = os.environ.copy()
    env["FLASK_PORT"] = str(EVE_PORT)
    env["DATA_DIR"] = os.path.join(LOCAL_DATA_DIR, "eve")
    env["LOG_DIR"] = env["DATA_DIR"]
    p = subprocess.Popen(prepend_cmd(start_cmd, "       eve", Color.CYAN.value),
                         env = env, cwd = start_dir, preexec_fn = os.setsid)
    return p

def stop_eve_process(p):
    lock_print("Stopping eve process.")
    os.killpg(os.getpgid(p.pid), signal.SIGTERM)

def start_redis_process(start_dir, start_cmd):
    lock_print("Starting redis process.")
    env = os.environ.copy()
    env["REDIS_PORT"] = str(REDIS_PORT)
    env["DATA_DIR"] = os.path.join(LOCAL_DATA_DIR, "redis")
    env["LOG_DIR"] = env["DATA_DIR"]
    p = subprocess.Popen(prepend_cmd(start_cmd, "     redis", Color.GREEN.value),
                         env = env, cwd = start_dir, preexec_fn = os.setsid)
    return p

def stop_redis_process(p):
    lock_print("Stopping redis process.")
    os.killpg(os.getpgid(p.pid), signal.SIGTERM)

def start_backend_process(start_dir, start_cmd):
    lock_print("Starting backend process.")
    env = os.environ.copy()
    env["EVE_SERVER"] = "http://localhost:{}".format(EVE_PORT)
    env["REDIS_SERVER"] = "localhost"
    env["REDIS_PORT"] = str(REDIS_PORT)
    env["DOCUMENT_IMAGE_DIR"] = os.path.join(LOCAL_DATA_DIR, "test_images")
    p = subprocess.Popen(prepend_cmd(start_cmd, "   backend", Color.BLUE.value),
                         env = env, cwd = start_dir, preexec_fn = os.setsid)
    return p

def stop_backend_process(p):
    lock_print("Stopping backend process.")
    os.killpg(os.getpgid(p.pid), signal.SIGTERM)

def start_frontend_annotation_process(start_dir, start_cmd):
    lock_print("Starting frontend annotation process.")
    p = subprocess.Popen(prepend_cmd(start_cmd, "  frontend", Color.MAGENTA.value),
                         cwd = start_dir, preexec_fn = os.setsid)
    return p

def stop_frontend_annotation_process(p):
    lock_print("Stopping frontend process.")
    os.killpg(os.getpgid(p.pid), signal.SIGTERM)

def start_pipeline(start_dir, start_cmd):
    lock_print("Starting pipeline process.")
    env = os.environ.copy()
    env["DATA_DIR"] = os.path.join(LOCAL_DATA_DIR, "pipelines")
    p = subprocess.Popen(prepend_cmd(start_cmd, " pipelines", Color.YELLOW.value),
                         env = env, cwd = start_dir, preexec_fn = os.setsid)
    return p

def stop_pipeline(p):
    lock_print("Stopping pipeline process.")
    os.killpg(os.getpgid(p.pid), signal.SIGTERM)

def main():
    docker = "--docker" in sys.argv
    eve_only = "--eve-only" in sys.argv
    backend_only = "--backend-only" in sys.argv
    auth_eve = "--auth-eve" in sys.argv

    if not os.path.isdir(LOCAL_DATA_DIR):
        os.makedirs(LOCAL_DATA_DIR)

    os.environ["PINE_LOGGING_CONFIG_FILE"] = os.path.join(DIR, "shared", "logging.python.dev.json")

    e = source_env_file()
    if ("AUTH_MODULE" not in os.environ or os.environ["AUTH_MODULE"] == "vegas") and "VEGAS_CLIENT_SECRET" not in e:
        lock_print("Please set VEGAS_CLIENT_SECRET in .env.")
        return 1

    set_version()

    eve_dir = os.path.join(DIR, "eve")
    eve_start = os.path.join(eve_dir, "dev_run.sh")
    if not os.path.isfile(eve_start):
        lock_print("Couldn't find eve start script: {}.".format(eve_start))
        return 1
    
    if not eve_only:
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
        if docker:
            backend_start = [backend_start, "--host=0.0.0.0"]

    if not eve_only and not backend_only:
        frontend_annotation_dir = os.path.join(DIR, "frontend", "annotation")
        frontend_annotation_start = os.path.join(frontend_annotation_dir, "dev_run.sh")
        if not os.path.isfile(frontend_annotation_start):
            lock_print("Couldn't find frontend start script: {}/".format(frontend_annotation_start))
            return 1
        if docker:
            frontend_annotation_start = [frontend_annotation_start, "--", "--host", "0.0.0.0"]

        pipeline_dir = os.path.join(DIR, "pipelines")
        pipeline_start = os.path.join(pipeline_dir, "dev_run.sh")

    eve_process = start_eve_process(eve_dir, eve_start)
    if not eve_only:
        redis_process = start_redis_process(redis_dir, redis_start)
        backend_process = start_backend_process(backend_dir, backend_start)
    if not eve_only and not backend_only:
        frontend_annotation_process = start_frontend_annotation_process(frontend_annotation_dir, frontend_annotation_start)
        pipeline_process = start_pipeline(pipeline_dir, pipeline_start)

    def signal_handler(sig, frame):
        lock_print("")
        if not eve_only and not backend_only:
            stop_pipeline(pipeline_process)
            stop_frontend_annotation_process(frontend_annotation_process)
        if not eve_only:
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
