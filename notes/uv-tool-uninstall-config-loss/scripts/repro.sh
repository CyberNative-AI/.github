#!/usr/bin/env bash
# Reproduce uv#22491 on Linux by giving uv the Windows default layout:
# user config and tools dir share one parent (<root>/uv/uv.toml, <root>/uv/tools).
# Usage: repro.sh <uv-version>
set -u
V="$1"; W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
export XDG_CONFIG_HOME="$W/appdata" UV_TOOL_DIR="$W/appdata/uv/tools" UV_TOOL_BIN_DIR="$W/bin" \
       UV_CACHE_DIR="$W/cache" UV_PYTHON_INSTALL_DIR="$W/pyinst" UV_NO_PROGRESS=1
UVBIN="$W/uvbin"; mkdir -p "$UVBIN"
env -u XDG_CONFIG_HOME UV_TOOL_DIR=/nonexistent uv pip install -q --target "$UVBIN" "uv==$V" >/dev/null 2>&1 || { echo "install uv $V failed"; exit 3; }
U="$UVBIN/bin/uv"
mkdir -p "$W/appdata/uv"
printf '[pip]\nindex-url = "https://example.invalid/simple"\n' > "$W/appdata/uv/uv.toml"
echo "== uv $($U --version)"
echo "-- config used before (expect example.invalid failure):"
echo cowsay | $U pip compile - --no-header 2>&1 | grep -o -m1 -E 'example\.invalid|cowsay==[0-9.]+'
$U tool install -q cowsay==6.1 >/dev/null 2>&1; echo "-- after install: $(ls "$W/appdata/uv" | tr '\n' ' ')"
$U tool uninstall cowsay 2>&1 | sed 's/^/   /'
echo "-- after uninstall of last tool: uv dir exists=$([ -d "$W/appdata/uv" ] && echo yes || echo no) uv.toml exists=$([ -f "$W/appdata/uv/uv.toml" ] && echo yes || echo no)"
echo "-- index used after (same command):"
echo cowsay | $U pip compile - --no-header 2>&1 | grep -o -m1 -E 'example\.invalid|cowsay==[0-9.]+'
