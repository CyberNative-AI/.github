#!/bin/bash
# One npm prefix per Node implementation under /envs/node (inside node:22-bookworm).
set -eu
export npm_config_cache=/tmp/npmc npm_config_update_notifier=false npm_config_fund=false npm_config_audit=false
mk(){ n=$1; shift; [ -d /envs/node/$n/node_modules ] && return 0; mkdir -p /envs/node/$n; cd /envs/node/$n; echo '{"name":"x","private":true,"type":"module"}' > package.json; npm install --save-exact --no-progress --loglevel=error "$@" >/dev/null; npm ls --all --json > npm-ls.json || true; echo "ok $n"; }
mk ts-sdk-1.29.0 @modelcontextprotocol/sdk@1.29.0 zod@3
mk ts-sdk-1.32.1 @modelcontextprotocol/sdk@1.32.1 zod@3
mk ts-v2-2.3.1 @modelcontextprotocol/client@2.3.1 @modelcontextprotocol/server@2.3.1 @modelcontextprotocol/node@2.1.1 zod@4
mk everything-2026.7.4 @modelcontextprotocol/server-everything@2026.7.4
mk everything-1.0.0 @modelcontextprotocol/server-everything@1.0.0
mk filesystem-2026.7.4 @modelcontextprotocol/server-filesystem@2026.7.4
mk filesystem-1.0.0 @modelcontextprotocol/server-filesystem@1.0.0
rm -rf /tmp/npmc
