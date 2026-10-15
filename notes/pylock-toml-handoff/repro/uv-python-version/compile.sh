#!/bin/sh
# Runs in python:3.12-slim. /in = fixture pyproject (ro), /out = lock output.
set -u
python -m pip install -q uv==0.13.1 2>&1 | grep -v notice
uv --version
mkdir -p /tmp/p && cp /in/pyproject.toml /tmp/p/ && cd /tmp/p
for sel in S0 S1 S2 M; do
  case $sel in
    S0) F="";; S1) F="--extra http";; S2) F="--group pyproject.toml:lint";;
    M) F="--all-extras --group pyproject.toml:lint --group pyproject.toml:dev";;
  esac
  mkdir -p /out/$sel
  uv pip compile pyproject.toml --universal --exclude-newer 2026-10-14T00:00:00Z --python-version 3.10 $F -o /out/$sel/pylock.toml -q 2>&1 | grep -v "experimental"
  echo "== $sel: $(grep -E '^(requires-python|environments)' /out/$sel/pylock.toml | tr '\n' ' ') packages: $(grep -E '^name' /out/$sel/pylock.toml | sed 's/name = //' | tr -d '"' | tr '\n' ' ')"
done
