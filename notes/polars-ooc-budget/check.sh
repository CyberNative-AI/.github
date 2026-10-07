#!/usr/bin/env bash
# Rerun: ./check.sh            (needs Docker, ~1.3 GB disk, about 13 minutes; TRIALS=N to change)
# Each trial runs query.py in a fresh container with a hard memory limit and
# no swap, then prints one JSON line. Exit 137 means SIGKILL: consistent with an
# OOM kill under this limit; the cause is not recorded. peak_var_tmp_kb comes
# from a du sample every 0.3 s, so short-lived spill growth can be missed.
set -u
cd "$(dirname "$0")"
DATA=$(mktemp -d)
trap 'rm -rf "$DATA"' EXIT

image() {  # image <polars version>
  printf 'FROM python:3.12-slim\nRUN pip install --no-cache-dir polars==%s numpy==2.3.4\n' "$1" |
    docker build -q -t "polars-ooc-check:$1" - >/dev/null 2>&1
}

trial() {  # trial <polars version> <memory limit> <label> [docker -e args...]
  local ver=$1 mem=$2 label=$3; shift 3
  rm -rf "$DATA/out" && mkdir -p "$DATA/out" && chmod 777 "$DATA/out"
  docker run --rm --memory="$mem" --memory-swap="$mem" --cpus=4 "$@" \
    -v "$DATA/in.parquet:/in.parquet:ro" -v "$DATA/out:/out" -v "$PWD/query.py:/query.py:ro" \
    "polars-ooc-check:$ver" sh -c '
      python /query.py /in.parquet /out/result.parquet > /out/log 2>&1 & p=$!; max=0
      while kill -0 $p 2>/dev/null; do
        s=$(du -sk /var/tmp 2>/dev/null | cut -f1); [ "$s" -gt "$max" ] && max=$s; sleep 0.3
      done
      wait $p; echo "$? $max $(tail -1 /out/log)"' > "$DATA/r"
  read -r code spill_kb rest < "$DATA/r"
  local ok=null
  if [ "$code" = 0 ]; then  # verify the output without a memory limit
    ok=$(docker run --rm -v "$DATA/out:/out:ro" "polars-ooc-check:$ver" python -c \
      'import polars as pl; d = pl.read_parquet("/out/result.parquet"); print(str(d.height == 40_000_000 and d["k"].is_sorted()).lower())')
  fi
  printf '{"polars":"%s","memory":"%s","setting":"%s","exit":%s,"peak_var_tmp_kb":%s,"sorted_40M_rows":%s,"log":"%s"}\n' \
    "$ver" "$mem" "$label" "$code" "$spill_kb" "$ok" "$rest"
}

image 2.0.0; image 1.44.2
docker run --rm -v "$DATA:/d" -v "$PWD/gen.py:/gen.py:ro" polars-ooc-check:2.0.0 \
  sh -c 'python /gen.py /d/in.parquet && chmod 644 /d/in.parquet'

for i in $(seq "${TRIALS:-10}"); do trial 2.0.0 1g default; done
for i in $(seq "${TRIALS:-10}"); do trial 2.0.0 1g POLARS_OOC_MEMORY_BUDGET_MB=500 -e POLARS_OOC_MEMORY_BUDGET_MB=500; done
trial 1.44.2 1g default
trial 2.0.0 1536m default
trial 1.44.2 1536m default
