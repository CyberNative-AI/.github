#!/bin/sh
# Build the image (once) and run the whole test offline. Results land in ./out; the last lines printed
# are the late-order counts for each way of planning.
#   ./rerun.sh                       default list vs Deadline-sorted list
#   ARMS="default deadline deadline_id deadline_id_desc" ./rerun.sh   also tie-break variants
set -eu
cd "$(dirname "$0")"
IMAGE=${IMAGE:-odoo20-plan-order:1}
docker image inspect "$IMAGE" >/dev/null 2>&1 || docker build -t "$IMAGE" .
mkdir -p out
docker run --rm --network none --user root \
  --tmpfs /tmp:rw,exec --tmpfs /var/lib/postgresql --tmpfs /var/run/postgresql --tmpfs /var/lib/odoo \
  -e ARMS="${ARMS:-default deadline}" -e HOST_UID="$(id -u)" -e HOST_GID="$(id -g)" \
  -v "$PWD:/bundle:ro" -v "$PWD/out:/out" --entrypoint /bin/bash "$IMAGE" /bundle/inside.sh
