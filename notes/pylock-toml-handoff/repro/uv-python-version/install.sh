#!/bin/sh
# Runs in python:3.10-slim-bookworm. /out = locks from compile.sh (ro).
set -u
python -m pip install -q pip==26.2.1 uv==0.13.1 2>&1 | grep -v notice
python -m pip --version; uv --version
for sel in S0 S1 S2 M; do
  for tool in pip uv; do
    d=/tmp/$sel-$tool; rm -rf $d; mkdir -p $d; cd $d; cp /out/$sel/pylock.toml .
    python -m venv v
    if [ $tool = pip ]; then v/bin/python -m pip install -q --upgrade pip==26.2.1 >/dev/null 2>&1; v/bin/python -m pip install -r pylock.toml > log 2>&1; rc=$?
    else uv pip install --python v/bin/python -r pylock.toml > log 2>&1; rc=$?; fi
    inst=$(v/bin/python -c "import importlib.metadata as m; print(sorted(d.metadata['Name']+'=='+d.version for d in m.distributions() if d.metadata['Name'] not in ('pip','setuptools','wheel')))")
    echo "RESULT sel=$sel tool=$tool rc=$rc installed=$inst"
    grep -E "^ERROR|^error" log | tail -2 | sed 's/^/    /'
  done
done
