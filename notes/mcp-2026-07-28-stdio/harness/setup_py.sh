#!/bin/bash
# Create one venv per Python implementation under /envs/py (inside node:22-bookworm, system Python 3.11.2), via uv.
set -eu
export UV_CACHE_DIR=/tmp/uvc
mk(){ n=$1; shift; [ -x /envs/py/$n/bin/python ] && return 0; /envs/uv venv -q -p /usr/bin/python3 /envs/py/$n; VIRTUAL_ENV=/envs/py/$n /envs/uv pip install -q "$@"; VIRTUAL_ENV=/envs/py/$n /envs/uv pip freeze > /envs/py/$n/freeze.txt; echo "ok $n"; }
mk mcp-2.3.0 mcp==2.3.0
mk mcp-1.30.0 mcp==1.30.0
mk mcp-1.28.1 mcp==1.28.1
mk mcp-1.12.4 mcp==1.12.4
mk fastmcp-4.1.0 fastmcp==4.1.0
mk fastmcp-3.4.8 fastmcp==3.4.8
mk fastmcp-2.14.0 fastmcp==2.14.0
rm -rf /tmp/uvc
