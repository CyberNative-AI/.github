export UV_CACHE_DIR=/scratch/uvc
for p in "1.8.1 2025-05-20" "1.9.4 2025-06-20" "1.10.1 2025-07-01" "1.11.0 2025-07-15"; do set -- $p; n=mcp-$1; /envs/uv venv -q -p /usr/bin/python3 /senv/py/$n && VIRTUAL_ENV=/senv/py/$n /envs/uv pip install -q --exclude-newer "$2T00:00:00Z" mcp==$1 && echo ok $n; done
