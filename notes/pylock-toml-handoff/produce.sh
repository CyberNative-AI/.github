#!/usr/bin/env bash
# Producer phase. Runs in python:3.12-slim; /x = this folder (ro), /w = work dir.
# Every command's exit code and stderr tail go to /w/locks/produce.jsonl; failures do not stop the phase.
set -u
B=/w/tools/venv3.12/bin
CUT=2026-10-14T00:00:00Z
OUT=/w/locks
LOG=$OUT/produce.jsonl
export HOME=/w/home UV_CACHE_DIR=/w/cache/uv PIP_CACHE_DIR=/w/cache/pip PDM_CACHE_DIR=/w/cache/pdm \
  POETRY_CACHE_DIR=/w/cache/poetry POETRY_VIRTUALENVS_CREATE=false UV_PYTHON_DOWNLOADS=never \
  PDM_CHECK_UPDATE=false PIP_DISABLE_PIP_VERSION_CHECK=1 PATH=$B:$PATH
mkdir -p $OUT /w/home /w/proj
: > $LOG

run() { # run <cell-id> <dir> cmd...
  local id=$1 dir=$2; shift 2
  local err; err=$(cd "$dir" && "$@" 2>&1 >/dev/null); local rc=$?
  python3 - "$id" "$rc" "$err" "$*" >> $LOG <<'PY'
import json, sys
print(json.dumps({"id": sys.argv[1], "rc": int(sys.argv[2]), "cmd": sys.argv[4], "stderr_tail": sys.argv[3][-1500:]}))
PY
}

fresh() { rm -rf "/w/proj/$1"; cp -r "/x/$2" "/w/proj/$1"; }

for fx in fixture fixture-env; do
  # ---- uv (uv.lock then export) ----
  P=uv-$fx; fresh $P $fx; D=/w/proj/$P
  run $P:lock $D uv lock --exclude-newer $CUT
  for sel in S0 S1 S2 M; do
    case $sel in
      S0) F="--no-default-groups";; S1) F="--no-default-groups --extra http";;
      S2) F="--no-default-groups --group lint";; M) F="--all-extras --all-groups";;
    esac
    mkdir -p $OUT/$P/$sel
    run $P:$sel:pylock $D uv export --frozen --no-emit-project $F --format pylock.toml -o $OUT/$P/$sel/pylock.toml
    run $P:$sel:req $D uv export --frozen --no-emit-project $F --format requirements.txt -o $OUT/$P/$sel/requirements.txt
  done
  [ $fx = fixture-env ] && continue
  # ---- uv pip compile --universal ----
  P=uvc-fixture; fresh $P fixture; D=/w/proj/$P
  for sel in S0 S1 S2 M; do
    case $sel in
      S0) F="";; S1) F="--extra http";; S2) F="--group pyproject.toml:lint";;
      M) F="--all-extras --group pyproject.toml:lint --group pyproject.toml:dev";;
    esac
    mkdir -p $OUT/$P/$sel
    run $P:$sel:pylock $D uv pip compile pyproject.toml --universal --exclude-newer $CUT $F -o $OUT/$P/$sel/pylock.toml
    run $P:$sel:req $D uv pip compile pyproject.toml --universal --generate-hashes --exclude-newer $CUT $F -o $OUT/$P/$sel/requirements.txt
  done
  # ---- pdm ----
  P=pdm-fixture; fresh $P fixture; D=/w/proj/$P
  run $P:lock $D pdm lock --exclude-newer $CUT -G :all
  for sel in S0 S1 S2 M; do
    case $sel in
      S0) F="--prod";; S1) F="--prod -G http";; S2) F="-G lint --without dev";; M) F="-G :all";;
    esac
    mkdir -p $OUT/$P/$sel
    run $P:$sel:pylock $D pdm export $F -f pylock -o $OUT/$P/$sel/pylock.toml
    run $P:$sel:req $D pdm export $F -f requirements -o $OUT/$P/$sel/requirements.txt
  done
  # ---- poetry (+ poetry-plugin-export) ----
  P=poetry-fixture; fresh $P fixture; D=/w/proj/$P
  run $P:lock $D poetry lock
  for sel in S0 S1 S2 M; do
    case $sel in
      S0) F="--only main";; S1) F="--only main --extras http";; S2) F="--with lint --without dev";;
      M) F="--all-extras --all-groups";;
    esac
    mkdir -p $OUT/$P/$sel
    run $P:$sel:pylock $D poetry export $F -f pylock.toml -o $OUT/$P/$sel/pylock.toml
    run $P:$sel:req $D poetry export $F -f requirements.txt -o $OUT/$P/$sel/requirements.txt
  done
  # ---- pip lock (single-use; equivalent requirement lists) ----
  P=pip-fixture; rm -rf /w/proj/$P; mkdir -p /w/proj/$P; D=/w/proj/$P
  printf 'click>=8.1\ntomli>=2; python_version < "3.11"\n' > $D/S0.in
  cp $D/S0.in $D/S1.in; echo 'requests>=2.31' >> $D/S1.in
  cp $D/S0.in $D/S2.in; echo 'mccabe>=0.7' >> $D/S2.in
  for sel in S0 S1 S2; do
    mkdir -p $OUT/$P/$sel
    run $P:$sel:pylock $D python -m pip lock --uploaded-prior-to $CUT -r $sel.in -o $OUT/$P/$sel/pylock.toml
  done
done
cp /w/proj/uv-fixture/uv.lock $OUT/uv-fixture/uv.lock 2>/dev/null
cp /w/proj/uv-fixture-env/uv.lock $OUT/uv-fixture-env/uv.lock 2>/dev/null
cp /w/proj/pdm-fixture/pdm.lock $OUT/pdm-fixture/pdm.lock 2>/dev/null
cp /w/proj/poetry-fixture/poetry.lock $OUT/poetry-fixture/poetry.lock 2>/dev/null
cd $OUT && find . -name '*.toml' -o -name '*.txt' -o -name '*.lock' | sort | xargs sha256sum > produced.sha256
echo done
