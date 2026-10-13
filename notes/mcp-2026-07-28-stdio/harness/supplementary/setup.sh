set -u
export UV_CACHE_DIR=/scratch/uvc npm_config_cache=/scratch/npmc npm_config_update_notifier=false npm_config_fund=false npm_config_audit=false
mk(){ n=$1; d=$2; shift 2; /envs/uv venv -q -p /usr/bin/python3 /senv/py/$n && VIRTUAL_ENV=/senv/py/$n /envs/uv pip install -q --exclude-newer "$d" "$@" && VIRTUAL_ENV=/senv/py/$n /envs/uv pip freeze > /senv/py/$n/freeze.txt && echo "ok $n"; }
mk mcp-1.2.1 2025-03-01T00:00:00Z mcp==1.2.1
mk mcp-1.6.0 2025-04-15T00:00:00Z mcp==1.6.0
mk fastmcp-2.2.0 2025-04-25T00:00:00Z fastmcp==2.2.0
mk fastmcp-2.10.6 2025-07-25T00:00:00Z fastmcp==2.10.6
for v in 1.7.0 1.12.0; do mkdir -p /senv/node/ts-sdk-$v && cd /senv/node/ts-sdk-$v && echo '{"name":"x","private":true,"type":"module"}' > package.json && npm install --save-exact --no-progress --loglevel=error @modelcontextprotocol/sdk@$v zod@3 >/dev/null && cp /supp/server_ts1.mjs . && echo "ok ts-sdk-$v"; done
