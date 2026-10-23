#!/bin/bash
# Run shapes.sh in both agent-home layouts and print one JSON line per shape.
# Old layout: user home /home/vsts. New (Ubuntu 26.04) layout: /home/runner, no /home/vsts.
# Same uid in both, read-only root, writable tmpfs only, no network.
# usage: UV=/path/to/uv bash run.sh [REPEATS]   (uv: a static Linux x86-64 binary; we used 0.10.7)
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
REPEATS=${1:-1}
UV=${UV:-$(command -v uv)}
DOCKER_RUN=${DOCKER_RUN:-docker run}
declare -A IMG=(
  [base]=ubuntu@sha256:c098726dd9b9733f3e885f8de0ef375206a311b0a317eadc40d347b1115fb944   # ubuntu 26.04
  [py]=python@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f     # python:3.13-slim (3.13.16)
  [node]=node@sha256:3d27e5c11e5786e309ec3e03f93ae536eb36e6e5eb3714d5eb3300a36157add0     # node:24 (24.21.0)
)
for r in $(seq 1 "$REPEATS"); do for set in base py node; do for layout in old new; do
  [ "$layout" = old ] && U=vsts || U=runner
  $DOCKER_RUN --rm --read-only --network none \
    --tmpfs /home:mode=755 --tmpfs "/home/$U:uid=1001,gid=1001,mode=755,exec" --tmpfs /tmp:mode=1777,exec \
    -u 1001:1001 -e HOME=/home/$U -e npm_config_update_notifier=false \
    -v "$HERE/shapes.sh:/opt/shapes.sh:ro" -v "$UV:/opt/uv:ro" \
    "${IMG[$set]}" bash /opt/shapes.sh "$layout" "$set" | sed "s/^{/{\"rep\":$r,/" | grep '^{'
done; done; done
