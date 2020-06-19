#!/bin/bash
set -e

SKIP_PERMISSION_FIX=${SKIP_PERMISSION_FIX:-0}
ROOT_DIR=${ROOT_DIR:-/nlp-web-app/pipelines}

if [[ ${SKIP_PERMISSION_FIX} = "0" ]]; then
    #echo "Fixing Permissions"
    for v in ${ROOT_DIR}; do
      chown -R nlp_user:nlp_user ${v}
      #echo "Changed ${v} Permissions to Active Learning"
    done
#else
    #echo "Skipped Fixing Permissions"
fi

#echo "Lowering Privileges and Starting Active Learning"
exec /usr/local/bin/gosu nlp_user "$@"
