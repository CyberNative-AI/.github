#!/bin/bash
# Runs inside ghcr.io/astral-sh/uv:0.13.5-python3.12-trixie-slim with /work. Network on (installs only).
set -u
export HOME=/work/home UV_CACHE_DIR=/work/home/.uv
mkdir -p $HOME /work/sites /work/logs
F=/work/fixtures; S=/work/sites
log(){ echo "[$(date -u +%H:%M:%S)] $*"; }
cd /work && rm -rf venv && UV_PYTHON_INSTALL_DIR=/work/home/py uv venv -q --python 3.13 venv && . venv/bin/activate
uv pip install -q mkdocs==1.6.1 mkdocs-material==9.8.0 sphinx==9.2.0 furo==2025.12.19 sphinx-rtd-theme==3.1.0 \
  pydata-sphinx-theme==0.23.0 sphinx-design==0.7.0 alabaster==1.0.0 pypdfium2==5.14.0 > /work/logs/py.log 2>&1; log "install rc=$?"
uv pip freeze > /work/logs/py.versions
for a in mkdocs mkdocs-material; do
  ( rm -rf $S/$a && cp -r $F/$a $S/$a && cd $S/$a && mkdocs build --strict ) > /work/logs/$a.log 2>&1; log "$a rc=$?"
done
for a in sphinx-alabaster sphinx-furo sphinx-sphinx-rtd-theme sphinx-pydata-sphinx-theme; do
  ( rm -rf $S/$a && cp -r $F/$a $S/$a && cd $S/$a && sphinx-build -q -b html . _build/html ) > /work/logs/$a.log 2>&1; log "$a rc=$?"
done
log done
