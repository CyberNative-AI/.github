#!/bin/bash
# Runs inside ghcr.io/astral-sh/uv:0.13.5-python3.12-trixie-slim after build_py.sh (which made /work/venv).
# usage: read.sh <pass dir under /work/out>   -> cells.json, read.txt, cells7.json in that dir
set -eu
/work/venv/bin/python -I /work/src/read.py "/work/out/$1" > "/work/out/$1/read.txt"
/work/venv/bin/python -I /work/src/posthoc_cells.py "/work/out/$1" > "/work/out/$1/cells7.json"
