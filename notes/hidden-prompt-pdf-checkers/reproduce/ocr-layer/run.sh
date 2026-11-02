#!/bin/bash
# Scanned-page follow-up (November 2). Run ../run.sh WORKDIR first: it builds the image and the
# tool environments this reuses. usage: ./run.sh WORKDIR   (writes WORKDIR/ocr)
set -euo pipefail
K=$(cd "$(dirname "$0")/.." && pwd); W=$(cd "$1" && pwd); mkdir -p "$W/ocr"
docker run --rm --network none --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$W/v:/v:ro" -v "$W/src:/src:ro" -v "$K:/w:ro" -v "$W/ocr:/o" \
  hidpdf-os bash /w/ocr-layer/check.sh /w/inputs/N1.pdf /o > "$W/ocr/run.txt" 2>&1
cat "$W/ocr/run.txt"
