#!/usr/bin/env bash
# Same Windows-like layout, managed-Python path: uv python uninstall of the last managed Python.
# Usage: repro-python.sh <uv-version>
set -u
V="$1"; W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
export XDG_CONFIG_HOME="$W/appdata" UV_PYTHON_INSTALL_DIR="$W/appdata/uv/python" UV_PYTHON_BIN_DIR="$W/bin" \
       UV_TOOL_DIR="$W/appdata/uv/tools" UV_CACHE_DIR="$W/cache" UV_NO_PROGRESS=1
UVBIN="$W/uvbin"; mkdir -p "$UVBIN"
env -u XDG_CONFIG_HOME -u UV_PYTHON_INSTALL_DIR uv pip install -q --target "$UVBIN" "uv==$V" >/dev/null 2>&1 || { echo "install uv $V failed"; exit 3; }
U="$UVBIN/bin/uv"
mkdir -p "$W/appdata/uv"
printf '[pip]\nindex-url = "https://example.invalid/simple"\n' > "$W/appdata/uv/uv.toml"
echo "== uv $($U --version)"
$U python install -q 3.12 >/dev/null 2>&1; echo "-- after python install: $(ls "$W/appdata/uv" | tr '\n' ' ')"
$U python uninstall --all 2>&1 | tail -1 | sed 's/^/   /'
echo "-- after uninstall of last managed Python: uv dir exists=$([ -d "$W/appdata/uv" ] && echo yes || echo no) uv.toml exists=$([ -f "$W/appdata/uv/uv.toml" ] && echo yes || echo no)"
