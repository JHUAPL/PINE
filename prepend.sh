#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

if [[ $# -lt 3 ]]; then
    echo "Usage: $0 <stdout prefix> <stderr prefix> <command> [<arg>...]"
    exit 1
fi

STDOUT_PREFIX="$1"
STDERR_PREFIX="$2"
shift 2
COMMAND=$@

prepend() {
    local line
    while read line; do
        printf '%b: %s\n' "$1" "$line"
    done
}

STDOUT=$(mktemp -u)
STDERR=$(mktemp -u)
mkfifo "$STDOUT" "$STDERR"
trap "rm -f \"$STDOUT\" \"$STDERR\"" EXIT

prepend "${STDOUT_PREFIX}" < "$STDOUT" >&1 &
prepend "${STDERR_PREFIX}" < "$STDERR" >&2 &
eval "$COMMAND" 1> "$STDOUT" 2> "$STDERR"
EXIT=$?

wait
exit $EXIT

