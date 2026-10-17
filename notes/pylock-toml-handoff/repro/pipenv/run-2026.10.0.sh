#!/bin/sh
# Runs inside python:3.10-slim-bookworm. /in holds A B C (read-only); work happens in /tmp.
set -u
python -m pip install -q pipenv==2026.10.0 2>&1 | tail -1
python -m pip --version; pipenv --version
for case in A B C; do
  for tool in pipenv pip; do
    d=/tmp/$case-$tool; rm -rf $d; mkdir -p $d; cp /in/$case/pylock.toml $d/; cd $d
    if [ $tool = pipenv ]; then
      PIPENV_VENV_IN_PROJECT=1 PIPENV_YES=1 PIPENV_NOSPIN=1 pipenv sync --python python3.10 > log 2>&1; rc=$?
      inst=$(.venv/bin/python -c "import importlib.metadata as m; print(sorted(d.metadata['Name']+'=='+d.version for d in m.distributions() if d.metadata['Name'] not in ('pip','setuptools','wheel')))" 2>/dev/null)
    else
      python -m venv v; v/bin/python -m pip install -q --upgrade pip==26.2.1 >/dev/null 2>&1
      v/bin/python -m pip install -r pylock.toml > log 2>&1; rc=$?
      inst=$(v/bin/python -c "import importlib.metadata as m; print(sorted(d.metadata['Name']+'=='+d.version for d in m.distributions() if d.metadata['Name'] not in ('pip','setuptools','wheel')))")
    fi
    echo "RESULT case=$case tool=$tool rc=$rc installed=$inst"
    grep -iE "error|warn|requires|environment" log | tail -3 | sed 's/^/    /'
  done
done
