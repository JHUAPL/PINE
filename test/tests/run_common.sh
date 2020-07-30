# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

if [[ -z ${DIR} ]]; then
    DIR="$( cd "$( dirname "${0}" )" && pwd )"
fi
export PINE_VERSION=$(${DIR}/../version.sh)

DOCKER_COMPOSE_FLAGS="-f docker-compose.yml -f docker-compose.override.yml -f docker-compose.test.yml"

export AUTH_MODULE=eve
export EVE_DB_VOLUME=eve_test_db

function setup() {

if [[ $1 == --stack ]]; then
    COMMAND="./docker_run.sh"
elif [[ $1 == --dashboard ]] || [[ $1 == --report ]]; then
    COMMAND="./docker_run.sh $@"
    if [[ $1 == --dashboard ]]; then
        DO_X="true"
    fi
elif [[ $1 == --bash ]]; then
    COMMAND="/bin/bash"
elif [[ $1 == --pytest ]]; then
    PYTEST="true"
else
    echo "Usage: $0 [--stack|--dashboard|--report|--bash]"
    echo "       --stack: Only run PINE"
    echo "       --dashboard: Run PINE and open the testing dashboard"
    echo "       --report: Run PINE and tests automated and generates videos and reports"
    echo "       --bash: Drop into a bash shell"
    echo "       --pytest: Run the pytest suite instead of cypress"
    exit 1
fi

if [[ $1 == --report ]] || [[ -n ${PYTEST} ]]; then
    export PINE_LOGGING_CONFIG_FILE="/nlp-web-app/shared/logging.python.json"
fi

set -ex

if [[ -n ${DO_X} ]]; then
    XSOCK=/tmp/.X11-unix
    XAUTH=$(mktemp -t .docker.xauth.XXXXXXXX)
    touch $XAUTH
    xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f $XAUTH nmerge -
    DOCKER_ARGS="--volume=$XSOCK:$XSOCK:rw \
                 --volume=$XAUTH:$XAUTH:rw \
                 --env=XAUTHORITY=${XAUTH} \
                 --env=DISPLAY"
fi

RESULTS_DIR=${RESULTS_DIR:-./results}
TIMESTAMP=$(date -Iseconds)

set +e

}

function cleanup() {

if [[ $1 == --report ]]; then
    mkdir -p ${RESULTS_DIR}/
    docker cp -a pine-cypress:/nlp_webapp/results ${RESULTS_DIR}/${TIMESTAMP}
fi

if [[ -n ${DO_X} ]]; then
    xauth nextract $XAUTH $DISPLAY
    rm $XAUTH
fi

}

function check_passed() {

if [[ $1 == --report ]]; then
    echo "Check ${RESULTS_DIR}/${TIMESTAMP} for results."
    if [[ $(cat ${RESULTS_DIR}/${TIMESTAMP}/reports/status) == PASSED ]]; then
        TEST_EXIT_CODE="0"
    else
        TEST_EXIT_CODE="1"
    fi
fi

}
