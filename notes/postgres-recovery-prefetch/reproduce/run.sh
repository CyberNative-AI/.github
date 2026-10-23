#!/bin/bash
# Plain-docker wrapper for gen.sh and replay.sh. Our runs started the same in-container scripts
# through our own job scheduler with these container limits (2 CPUs, 1 GiB memory, no swap).
# This wrapper was written for publication; it is not the launcher that produced results/.
#
# usage: WORK=/path/on/disk/under/test ./run.sh IMAGE gen TAG FPW          (FPW: on|off)
#        WORK=... ./run.sh IMAGE replay TAG PF REP [docker run options]    (PF: try|off)
#        WORK=... ./run.sh IMAGE collect OUTDIR
# Per-IO read cap, as in our capped runs: add  --device-read-iops /dev/sdX:300  (the disk under WORK).
# Source build (Dockerfile.src): IMAGE=pg186src and add
#   -e PATH=/opt/pgp/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin   (patched)
#   -e PATH=/opt/pgv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin   (vanilla)
set -euo pipefail
cd "$(dirname "$0")"
WORK=${WORK:?set WORK to an empty folder on the disk under test (about 13 GB per WAL set)}
IMG=$1; STEP=$2; shift 2
LIMITS=(--rm --cpus 2 --memory 1g --memory-swap 1g -v "$WORK:/work" -v "$PWD:/src:ro")
case $STEP in
  gen) docker run "${LIMITS[@]}" "$IMG" bash /src/gen.sh "$1" 200 "$2" ;;
  replay)
    TAG=$1; PF=$2; REP=$3; shift 3
    D=/work/$TAG/runs/$PF-$REP
    docker run "${LIMITS[@]}" "$@" "$IMG" bash -c "mkdir -p $D && command -v postgres > $D/binary && postgres -V >> $D/binary && cat /sys/fs/cgroup/io.max > $D/iomax && bash /src/replay.sh $TAG $PF $REP" ;;
  collect)
    mkdir -p "$1"; docker run --rm -v "$WORK:/work:ro" -v "$(realpath "$1"):/out" -v "$PWD:/src:ro" "$IMG" bash /src/collect.sh ;;
  *) echo "unknown step $STEP" >&2; exit 2 ;;
esac
