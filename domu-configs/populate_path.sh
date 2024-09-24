#!/bin/bash
set -euxo pipefail

ARTIFACT_ROOT=`pwd`
find domu-configs -name "*.cfg" | xargs sed -i "s/__ARTIFACT_ROOT__/${ARTIFACT_ROOT//\//\\\/}/"

