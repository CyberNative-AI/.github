#!/bin/sh
# Run docker-node's stackbrew.js, unchanged, at commit 84410eea with the clock set to each date.
# Usage: sh run-generator.sh OUTDIR   (needs git and docker; the container has no network)
set -eu
OUT=$(mkdir -p "$1" && cd "$1" && pwd)
HERE=$(cd "$(dirname "$0")" && pwd)
SRC="$OUT/docker-node"
[ -d "$SRC" ] || git clone -q https://github.com/nodejs/docker-node.git "$SRC"
git -C "$SRC" checkout -q 84410eeaede25daf49826da8265fbf548cc604fe
docker run --rm --network none -v "$SRC:/dn:ro" -v "$HERE:/src:ro" -v "$OUT:/work" node:24 sh -c '
  git config --global --add safe.directory "*"; cd /dn
  for d in 2026-10-22 2026-10-27 2026-10-28 2026-10-29 2026-11-15; do for rep in 1 2; do
    TZ=UTC FAKE_NOW=${d}T12:00:00Z node --require /src/fakedate.js ./stackbrew.js > /work/sim-$d-r$rep.txt
  done; done'
echo "outputs in $OUT; score with: python3 $HERE/score.py $OUT $HERE/library-node-live-20261022.txt"
