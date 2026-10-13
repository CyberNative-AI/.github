"""Spec-shaped synthetic stdio MCP servers (stdlib only) for mcp-stdio-cross-era controls and the legacy-shape arm.

usage: python3 fake_server.py MODE
MODE:
  modern        2026-07-28 only: answers server/discover; rejects initialize with UnsupportedProtocolVersionError (-32022)
  dual          answers server/discover (modern) and initialize (legacy 2025-11-25)
  legacy_32602  legacy; unknown pre-initialize request -> -32602 (spec names -32601/-32602 as common)
  legacy_silent legacy; ignores any pre-initialize request (no reply) — the "does not respond" probe outcome
  legacy_exit   legacy; exits (rc 1) on any pre-initialize request — outcome the spec does not list
All modes expose one tool `echo` returning `echo:<message>`.
"""

import json
import sys

MODERN = "2026-07-28"
LEGACY = "2025-11-25"
TOOL = {"name": "echo", "description": "Echo the message",
        "inputSchema": {"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"]}}
INFO = {"name": "echo-server", "version": "1.0.0"}


def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def main():
    mode = sys.argv[1]
    modern_ok = mode in ("modern", "dual")
    legacy_ok = mode != "modern"
    initialized = False
    for raw in sys.stdin:
        try:
            msg = json.loads(raw)
        except ValueError:
            continue
        mid, method = msg.get("id"), msg.get("method")
        params = msg.get("params") or {}
        meta = params.get("_meta") or {}
        is_modern_req = "io.modelcontextprotocol/protocolVersion" in meta
        if mid is None:
            if method == "notifications/initialized" and legacy_ok:
                initialized = True
            continue
        if method == "initialize":
            if not legacy_ok:
                send({"jsonrpc": "2.0", "id": mid, "error": {"code": -32022, "message": "Unsupported protocol version; supported: " + MODERN,
                                                               "data": {"supported": [MODERN], "requested": params.get("protocolVersion")}}})
                continue
            send({"jsonrpc": "2.0", "id": mid, "result": {"protocolVersion": LEGACY, "capabilities": {"tools": {}}, "serverInfo": INFO}})
            continue
        if modern_ok and (method == "server/discover" or (is_modern_req and not initialized)):
            if method == "server/discover":
                send({"jsonrpc": "2.0", "id": mid, "result": {"resultType": "complete", "supportedVersions": [MODERN], "capabilities": {"tools": {}},
                                                               "_meta": {"io.modelcontextprotocol/serverInfo": INFO}, "ttlMs": 0, "cacheScope": "private"}})
                continue
            res = handle(method, params)
            if res is None:
                send({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "Method not found"}})
            else:
                res = dict(res, resultType="complete", _meta={"io.modelcontextprotocol/serverInfo": INFO})
                if method == "tools/list":
                    res.update(ttlMs=0, cacheScope="private")
                send({"jsonrpc": "2.0", "id": mid, "result": res})
            continue
        if not initialized:
            if mode == "legacy_silent":
                continue
            if mode == "legacy_exit":
                sys.exit(1)
            code = -32602 if mode == "legacy_32602" else -32601
            send({"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": "Server not initialized"}})
            continue
        res = handle(method, params)
        if res is None:
            send({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "Method not found"}})
        else:
            send({"jsonrpc": "2.0", "id": mid, "result": res})


def handle(method, params):
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": [TOOL]}
    if method == "tools/call" and params.get("name") == "echo":
        return {"content": [{"type": "text", "text": "echo:" + str((params.get("arguments") or {}).get("message"))}], "isError": False}
    return None


if __name__ == "__main__":
    main()
