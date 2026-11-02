#!/bin/bash
# Rerun the whole test: fetch the two GitHub tools at the tested commits, build the image and venvs
# (network), run every PDF offline, score, and recount. Needs docker, git, curl, python3 with Pillow.
# usage: ./run.sh WORKDIR    (WORKDIR gets ~5 GB: venvs, model cache, renders)
set -euo pipefail
K=$(cd "$(dirname "$0")" && pwd); W=$(mkdir -p "$1" && cd "$1" && pwd)
mkdir -p "$W/src" "$W/v" "$W/o"
fetch() {  # repo commit dir
  [ -d "$W/src/$3" ] && return
  git clone -q "https://github.com/$1" "$W/src/$3" && git -C "$W/src/$3" checkout -q "$2"
}
fetch tobycmurray/phantom-lint 7f6200145abf9d1592118780e117d14541a18dae phantom-lint
fetch wppoland/hidden-text-detector ce9e505dc1c128701e921e8d7e1a133c7ff28db8 hidden-text-detector
cp "$K/image/setup-venvs.sh" "$W/src/"
docker build -t hidpdf-os "$K/image"
U="--user $(id -u):$(id -g) -e HOME=/tmp -e HF_HOME=/v/hf"
docker run --rm $U -v "$W/v:/v" -v "$W/src:/src:ro" -e TMPDIR=/tmp hidpdf-os bash /src/setup-venvs.sh
docker run --rm --network none $U -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 \
  -v "$W/v:/v:ro" -v "$W/src:/src:ro" -v "$K:/w:ro" -v "$W/o:/o" \
  hidpdf-os python -I /w/src/run.py /w/inputs /o
python3 -I "$K/src/score.py" "$K/inputs" "$W/o"
python3 -I "$K/src/recount.py" "$W/o"
