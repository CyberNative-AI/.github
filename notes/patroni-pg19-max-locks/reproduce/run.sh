#!/bin/bash
# Run one script from this folder in a throwaway container. Usage: ./run.sh NAME IMAGE SCRIPT [ARGS...]
# SCRIPT is called as: SCRIPT NAME ARGS...
# The scripts run as root with trust authentication, so they run only inside this container:
# no network, data in tmpfs, 2 CPUs, 6 GiB memory with no swap, 1024 processes, this folder
# read-only and a new ./out/NAME as the only writable path. The script is stopped after
# DEADLINE seconds (default 1200), and the container is removed on exit, Ctrl-C or timeout.
set -eu
NAME=$1 IMAGE=$2 SCRIPT=$3; shift 3
HERE=$(cd "$(dirname "$0")" && pwd)
OUT="$HERE/out/$NAME"
mkdir -p "$HERE/out"; mkdir "$OUT"; chmod 777 "$OUT"   # refuses an existing ./out/NAME
CTR="pg19-locks-$NAME-$$"
trap 'docker rm -f "$CTR" >/dev/null 2>&1 || true' EXIT
trap 'exit 130' INT TERM
docker run --rm --name "$CTR" --network none \
  --cpus 2 --memory 6g --memory-swap 6g --pids-limit 1024 \
  --tmpfs /pgdata:rw,size=3g,mode=0755 -v "$HERE":/scripts:ro -v "$OUT":/out \
  --entrypoint timeout "$IMAGE" -k 10 "${DEADLINE:-1200}" /bin/bash "/scripts/$SCRIPT" "$NAME" "$@"
