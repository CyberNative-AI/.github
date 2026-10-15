#!/bin/sh
set -u
python -m pip install -q uv==0.13.1 2>&1 | grep -v notice
uv --version
mkdir -p /tmp/p && cp /in/pyproject.toml /tmp/p/ && cd /tmp/p
for extra in "" "--python-version 3.10"; do
  echo "== uv pip compile pyproject.toml --universal --exclude-newer 2026-10-14T00:00:00Z $extra --format pylock.toml"
  uv pip compile pyproject.toml --universal --exclude-newer 2026-10-14T00:00:00Z $extra --format pylock.toml -o pylock.toml -q 2>&1 | grep -v "^warning: The .--pylock\|experimental" 
  grep -E '^(requires-python|environments)|^name|^marker' pylock.toml
done
