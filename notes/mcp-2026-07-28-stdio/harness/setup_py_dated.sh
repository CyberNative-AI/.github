#!/bin/bash
# Rebuild the two old venvs with dependency resolution as of each release date (uv --exclude-newer):
# a plain install today resolves pydantic 2.14 (mcp 1.12.4 import error) and mcp 2.3.0 (fastmcp 2.14.0 import error).
set -eu
export UV_CACHE_DIR=/tmp/uvc
mk(){ n=$1; d=$2; shift 2; /envs/uv venv -q -p /usr/bin/python3 /envs/py/$n; VIRTUAL_ENV=/envs/py/$n /envs/uv pip install -q --exclude-newer "$d" "$@"; VIRTUAL_ENV=/envs/py/$n /envs/uv pip freeze > /envs/py/$n/freeze.txt; echo "ok $n"; }
mk mcp-1.12.4 2025-08-08T00:00:00Z mcp==1.12.4
mk fastmcp-2.14.0 2025-12-12T00:00:00Z fastmcp==2.14.0
rm -rf /tmp/uvc
