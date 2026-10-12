#!/bin/bash
# sp.sh NAME IMAGE SETUP_PYTHON_DIR SPEC [FILE_SPEC]
# Runs actions/setup-python's released dist (node24) inside a plain Ubuntu container with the
# environment a hosted runner gives an action, then runs the selected interpreter.
# SPEC goes to INPUT_PYTHON-VERSION; if FILE_SPEC is set, SPEC is ignored and FILE_SPEC is written
# to .python-version and passed as INPUT_PYTHON-VERSION-FILE.
# Mounts: $NODE (node binary), the setup-python checkout (ro). Output: logs/NAME.log, logs/NAME.rc
set -u
NAME=$1 IMAGE=$2 SP=$3 SPEC=$4 FILE_SPEC=${5:-}
H=$(cd "$(dirname "$0")" && pwd)
: "${NODE:?path to node binary}"
docker run --rm --memory 1g --cpus 2 -v "$NODE":/node:ro -v "$SP":/sp:ro \
  -e "INPUT_PYTHON-VERSION=$SPEC" -e "FILE_SPEC=$FILE_SPEC" -e INPUT_ARCHITECTURE=x64 \
  -e INPUT_CHECK-LATEST=false -e INPUT_UPDATE-ENVIRONMENT=true -e INPUT_ALLOW-PRERELEASES=false \
  -e INPUT_FREETHREADED=false -e INPUT_TOKEN= -e RUNNER_TOOL_CACHE=/opt/hostedtoolcache \
  -e RUNNER_TEMP=/tmp/runner -e RUNNER_OS=Linux -e RUNNER_ARCH=X64 -e GITHUB_ACTIONS=true \
  -e GITHUB_WORKSPACE=/work -e AGENT_TOOLSDIRECTORY=/opt/hostedtoolcache \
  "$IMAGE" bash -c '
    set -u; mkdir -p /opt/hostedtoolcache /tmp/runner /work /gh; cd /work
    export GITHUB_OUTPUT=/gh/out GITHUB_ENV=/gh/env GITHUB_PATH=/gh/path GITHUB_STATE=/gh/state
    touch /gh/out /gh/env /gh/path /gh/state
    if [ -n "$FILE_SPEC" ]; then echo "$FILE_SPEC" > .python-version; fi
    grep PRETTY_NAME /etc/os-release
    echo "spec=${FILE_SPEC:-$(printenv INPUT_PYTHON-VERSION)} file=${FILE_SPEC:+.python-version}"
    if [ -n "$FILE_SPEC" ]; then env -u INPUT_PYTHON-VERSION "INPUT_PYTHON-VERSION-FILE=.python-version" /node /sp/dist/setup/index.js; else /node /sp/dist/setup/index.js; fi
    rc=$?; echo "setup-python rc=$rc"
    echo "-- outputs:"; cat /gh/out | tr "\n" " "; echo
    P=$(head -1 /gh/path)
    if [ $rc -eq 0 ] && [ -n "$P" ]; then PATH="$P:$PATH" python -c "import sys; print(\"python\", sys.version.split()[0])"; fi
    exit $rc' > "$H/logs/$NAME.log" 2>&1
rc=$?; echo $rc > "$H/logs/$NAME.rc"; echo "$NAME rc=$rc"
