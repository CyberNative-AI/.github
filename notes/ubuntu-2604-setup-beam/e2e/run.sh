#!/bin/bash
# Run erlef/setup-beam's released dist/index.js in ubuntu:26.04 and ubuntu:24.04 containers, with
# the hosted runner's ImageOS value and an empty tool cache, for the five cases in the note.
#
# usage: e2e/run.sh NODE NEW_ACTION_DIR OLD_ACTION_DIR
#   NODE            a node 24 binary for linux x64 (the runner uses node 24), e.g. from node:24:
#                   docker create --name n node:24 && docker cp n:/usr/local/bin/node ./node && docker rm n
#   NEW_ACTION_DIR  git clone --depth 1 --branch v1.24.1 https://github.com/erlef/setup-beam
#   OLD_ACTION_DIR  the same at v1.24.0 (commit fc68ffb), which has no 26.04 mapping
# Needs Docker and network access to builds.hex.pm. Prints one block per case with the action's
# error or the installed version, the exit status, and `erl` output when OTP was installed.
set -u
if [ "${1:-}" = "--inner" ]; then  # inside the container: --inner IMAGEOS OTP_VERSION
  export RUNNER_TEMP=/tc/tmp RUNNER_TOOL_CACHE=/tc/cache GITHUB_WORKSPACE=/tc/ws RUNNER_OS=Linux RUNNER_ARCH=X64
  export ImageOS="$2" GITHUB_OUTPUT=/tc/out GITHUB_PATH=/tc/path GITHUB_ENV=/tc/env GITHUB_STATE=/tc/state
  mkdir -p "$RUNNER_TEMP" "$RUNNER_TOOL_CACHE" "$GITHUB_WORKSPACE"; : > /tc/out; : > /tc/path; : > /tc/env; : > /tc/state
  cd "$GITHUB_WORKSPACE"
  # every input the action declares with a default must be set, as the runner does
  env "INPUT_OTP-VERSION=$3" "INPUT_VERSION-TYPE=loose" "INPUT_INSTALL-HEX=true" "INPUT_INSTALL-REBAR=true" \
      "INPUT_HEXPM-MIRRORS=https://builds.hex.pm" "INPUT_OTP-ARCHITECTURE=64" "INPUT_DISABLE_PROBLEM_MATCHERS=false" \
      /node /action/dist/index.js > /tc/log 2>&1
  rc=$?
  grep -E "::error|Installing Erlang" /tc/log | head -3
  echo "exit status $rc"
  erl=$(find /tc -path '*/bin/erl' -type f 2>/dev/null | head -1)
  [ -n "$erl" ] && "$erl" -noshell -eval 'io:format("erl runs: OTP ~s~n",[erlang:system_info(otp_release)]), halt().'
  exit 0
fi
[ $# -eq 3 ] || { sed -n '2,13p' "$0"; exit 2; }
NODE=$(realpath "$1") NEW=$(realpath "$2") OLD=$(realpath "$3") SELF=$(realpath "$0")
echo "node $("$NODE" --version); new $(git -C "$NEW" rev-parse --short=7 HEAD); old $(git -C "$OLD" rev-parse --short=7 HEAD)"
run() {  # label image ImageOS action-dir otp-version
  echo "## $1: $2, ImageOS=$3, setup-beam $(git -C "$4" rev-parse --short=7 HEAD), otp-version $5"
  docker run --rm --tmpfs /tc:exec -v "$NODE:/node:ro" -v "$4:/action:ro" -v "$SELF:/run.sh:ro" "$2" \
    bash /run.sh --inner "$3" "$5"
}
run A ubuntu:26.04 ubuntu26 "$NEW" 25
run B ubuntu:26.04 ubuntu26 "$OLD" 27
run C ubuntu:24.04 ubuntu24 "$OLD" 27
run D ubuntu:24.04 ubuntu24 "$NEW" 25
run E ubuntu:26.04 ubuntu26 "$NEW" 27
