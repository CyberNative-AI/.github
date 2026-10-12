#!/bin/bash
# rr.sh NAME IMAGE SETUP_RUBY_DIR SPEC [STUB]
# Runs ruby/setup-ruby's dist (node24) in a plain Ubuntu container with a hosted runner's action
# environment and an empty tool cache. SPEC goes to INPUT_RUBY-VERSION. STUB (optional) is a file
# in stubs/ preloaded with node --require. Output: logs/NAME.log and logs/NAME.rc
set -u
NAME=$1 IMAGE=$2 SR=$3 SPEC=$4 STUB=${5:-}
H=$(cd "$(dirname "$0")" && pwd)
: "${NODE:?path to node binary}"
docker run --rm --memory 1g --cpus 2 -v "$NODE":/node:ro -v "$SR":/sr:ro -v "$H/stubs":/stubs:ro \
  -e "INPUT_RUBY-VERSION=$SPEC" -e "STUB=$STUB" -e INPUT_BUNDLER=default -e INPUT_BUNDLER-CACHE=false \
  -e INPUT_WORKING-DIRECTORY=. -e INPUT_CACHE-VERSION=0 -e INPUT_SELF-HOSTED=false \
  -e RUNNER_TOOL_CACHE=/opt/hostedtoolcache -e RUNNER_TEMP=/tmp/runner -e RUNNER_OS=Linux -e RUNNER_ARCH=X64 \
  -e GITHUB_ACTIONS=true -e GITHUB_WORKSPACE=/work \
  "$IMAGE" bash -c '
    set -u; mkdir -p /opt/hostedtoolcache /tmp/runner /work /gh; cd /work
    export GITHUB_OUTPUT=/gh/out GITHUB_ENV=/gh/env GITHUB_PATH=/gh/path GITHUB_STATE=/gh/state
    touch /gh/out /gh/env /gh/path /gh/state
    grep PRETTY_NAME /etc/os-release; echo "spec=$(printenv INPUT_RUBY-VERSION) stub=${STUB:-none}"
    if [ -n "$STUB" ]; then /node --require "/stubs/$STUB" /sr/dist/index.js; else /node /sr/dist/index.js; fi
    rc=$?; echo "setup-ruby rc=$rc"; echo "-- outputs:"; tr "\n" " " < /gh/out; echo
    exit $rc' > "$H/logs/$NAME.log" 2>&1
rc=$?; echo $rc > "$H/logs/$NAME.rc"; echo "$NAME rc=$rc"
