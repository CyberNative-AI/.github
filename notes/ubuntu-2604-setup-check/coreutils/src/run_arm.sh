#!/bin/bash
# usage: run_arm.sh ARM CASES OUT   (ARM: gnu94 -> coreutils2604:2404; uutils|gnu97 -> coreutils2604:2604)
set -euo pipefail
arm=$1; cases=$(realpath "$2"); out=$3; d=$(cd "$(dirname "$0")/.." && pwd)
img=coreutils2604:2604; [ "$arm" = gnu94 ] && img=coreutils2604:2404
mkdir -p "$(dirname "$out")"; touch "$out"; out=$(realpath "$out")
docker run --rm --name "coreutils2604-$arm-$$" --network none --user "$(id -u):$(id -g)" --memory 1g --cpus 2 --pids-limit 256 \
  --tmpfs /work:exec,size=512m,uid=$(id -u),gid=$(id -g) -v "$d/src:/src:ro" -v "$cases:/cases.jsonl:ro" -v "$out:/out.jsonl" \
  "$img" timeout -k 10 3000 python3 /src/harness.py "$arm" /cases.jsonl /out.jsonl
