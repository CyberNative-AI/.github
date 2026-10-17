#!/bin/sh
# Usage (inside python:3.15.0-slim, with network): install_envs.sh CASES_TSV ENVS_DIR
# One venv per package line of CASES_TSV: binary wheels only, index frozen at 2026-10-17T00:00:00Z.
set -u
cases=$1; envs=$2
export HOME=/tmp UV_CACHE_DIR=/tmp/uv-cache
python -m pip install --quiet --no-cache-dir --target /tmp/uv "uv==0.13.1" || exit 2
uv() { PYTHONPATH=/tmp/uv python -m uv "$@"; }
grep -v '^#' "$cases" | cut -f2 | sort -u | while read -r pkg; do
  venv=${pkg%%==*}
  uv venv --quiet --python /usr/local/bin/python3.15 "$envs/$venv" &&
    uv pip install --quiet --python "$envs/$venv/bin/python" --no-build \
      --exclude-newer 2026-10-17T00:00:00Z "$pkg" &&
    uv pip freeze --python "$envs/$venv/bin/python" > "$envs/$venv.freeze.txt"
  echo "$venv rc=$?"
done
