#!/bin/bash
# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

set -ex

if [[ $# -eq 0 ]]; then
  VERSION=$(curl --silent "https://api.github.com/repos/swagger-api/swagger-ui/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
  if [[ ${VERSION} = v* ]]; then
    VERSION=${VERSION:1}
  fi
else
  VERSION="$1"
fi

if [[ ! -f swagger-ui-${VERSION}.tar.gz ]]; then
  wget "https://github.com/swagger-api/swagger-ui/archive/refs/tags/v${VERSION}.tar.gz" -O swagger-ui-${VERSION}.tar.gz
fi

rm -rf swagger-ui/
tar xzf swagger-ui-${VERSION}.tar.gz swagger-ui-${VERSION}/dist/ --transform "s|swagger-ui-${VERSION}/dist|swagger-ui|"
sed -i 's|https://petstore.swagger.io/v2/swagger.json|{{spec_url}}|' swagger-ui/index.html
echo ${VERSION} > swagger-ui/VERSION
