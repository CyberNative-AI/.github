#!/bin/bash
# copy gen.json + run outputs (no data files) to /out, readable by the host user
set -euo pipefail
for d in /work/*/; do t=$(basename "$d"); [ -f "$d/gen.json" ] || continue
  mkdir -p "/out/$t"; cp "$d/gen.json" "/out/$t/"; [ -d "$d/runs" ] && cp -r "$d/runs" "/out/$t/"; done
chown -R 1000:1000 /out; chmod -R a+rX /out
