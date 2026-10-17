#!/bin/sh
# Inside python:3.15.0-slim with network. Args: list file of projects. Writes /w/envs/<p>, /w/install/<p>.log/.rc
set -u
LIST="$1"
export HOME=/w/home UV_CACHE_DIR=/w/uvcache UV_LINK_MODE=hardlink
mkdir -p /w/home /w/uvcache /w/envs /w/install /w/tools
if [ ! -x /w/tools/bin/uv ]; then
  python -m pip install --quiet --no-cache-dir --target /w/tools/lib "uv==0.13.1" >/w/install/_uv.log 2>&1 || { echo "uv install failed"; cat /w/install/_uv.log; exit 2; }
  mkdir -p /w/tools/bin && ln -sf /w/tools/lib/bin/uv /w/tools/bin/uv
fi
UV=/w/tools/bin/uv
$UV --version > /w/install/_uv.version
while read -r p; do
  [ -z "$p" ] && continue
  [ -f "/w/install/$p.rc" ] && continue
  rm -rf "/w/envs/$p"
  { $UV venv --quiet --python /usr/local/bin/python3.15 "/w/envs/$p" && \
    timeout 300 $UV pip install --python "/w/envs/$p/bin/python" --no-build \
      --exclude-newer 2026-10-17T00:00:00Z "$p"; } > "/w/install/$p.log" 2>&1
  echo $? > "/w/install/$p.rc"
done < "$LIST"
