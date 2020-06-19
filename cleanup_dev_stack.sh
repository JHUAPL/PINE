#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

ps ax | grep 'nlp\|ng \|npm\|flask\|virtualenv\|redis\|mongo' | grep -v 'grep\|avahi'
