"""Raw, SDK-independent era probe of a stdio MCP server (stdlib only).

usage: python3 probe_era.py OUT.json -- SERVER_CMD [ARGS...]

Two fresh server processes per call:
  A) modern-first: send `server/discover` (2026-07-28 shape, _meta with protocol version and
     client capabilities). Record the reply (result / error code / no reply in 5 s / process exit).
  B) legacy-first: send `initialize` (protocolVersion 2025-11-25), then `notifications/initialized`,
     then `tools/list`. Record replies.
Era label (frozen in PROTOCOL.md):
  modern_capable = A returns a JSON-RPC result containing `supportedVersions` that includes 2026-07-28
  legacy_capable = B returns an initialize result with a `protocolVersion` and tools/list returns a result
  DUAL = both, MODERN_ONLY = A only, LEGACY_ONLY = B only, NEITHER = none.
For A also record the failure shape a dual-era client must classify: error code/message,
silence (timeout), or process exit.
"""

import json
import os
import selectors
import subprocess
import sys
import time

MODERN = "2026-07-28"
LEGACY = "2025-11-25"
WAIT_S = 5.0


def exchange(cmd, messages, wait_ids):
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
    sel = selectors.DefaultSelector()
    sel.register(proc.stdout, selectors.EVENT_READ)
    replies, lines, buf = {}, [], b""
    t0 = time.monotonic()
    try:
        for msg in messages:
            proc.stdin.write((json.dumps(msg) + "\n").encode())
            proc.stdin.flush()
            want = msg.get("id")
            if want is None:
                continue
            deadline = time.monotonic() + WAIT_S
            while want not in replies and time.monotonic() < deadline:
                if proc.poll() is not None and not sel.select(0):
                    break
                for _key, _ in sel.select(timeout=0.1):
                    chunk = os.read(proc.stdout.fileno(), 65536)
                    if not chunk:
                        break
                    buf += chunk
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        text = line.decode("utf-8", "replace")
                        lines.append({"t_ms": round((time.monotonic() - t0) * 1000, 1), "line": text[:2000]})
                        try:
                            obj = json.loads(text)
                        except ValueError:
                            continue
                        if isinstance(obj, dict) and "id" in obj and ("result" in obj or "error" in obj):
                            replies[obj["id"]] = obj
            if want not in replies:
                replies[want] = {"_no_reply": True, "exited": proc.poll() is not None, "rc": proc.poll()}
    except (BrokenPipeError, OSError) as exc:
        replies.setdefault("_pipe", {"error": repr(exc)})
    finally:
        sel.close()
        try:
            proc.stdin.close()
        except OSError:
            pass
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    return {"replies": {str(k): v for k, v in replies.items()}, "lines": lines, "rc": proc.returncode}


def main():
    out = sys.argv[1]
    assert sys.argv[2] == "--"
    cmd = sys.argv[3:]
    meta = {
        "io.modelcontextprotocol/protocolVersion": MODERN,
        "io.modelcontextprotocol/clientCapabilities": {},
        "io.modelcontextprotocol/clientInfo": {"name": "re13340-probe", "version": "0"},
    }
    a = exchange(cmd, [{"jsonrpc": "2.0", "id": 1, "method": "server/discover", "params": {"_meta": meta}}], [1])
    b = exchange(
        cmd,
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": LEGACY, "capabilities": {}, "clientInfo": {"name": "re13340-probe", "version": "0"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        ],
        [1, 2],
    )
    ra = a["replies"].get("1", {})
    res_a = ra.get("result") or {}
    sv = res_a.get("supportedVersions") or []
    modern_capable = isinstance(sv, list) and MODERN in sv
    rb1, rb2 = b["replies"].get("1", {}), b["replies"].get("2", {})
    legacy_capable = bool((rb1.get("result") or {}).get("protocolVersion")) and "result" in rb2
    era = {(True, True): "DUAL", (True, False): "MODERN_ONLY", (False, True): "LEGACY_ONLY", (False, False): "NEITHER"}[(modern_capable, legacy_capable)]
    if "result" in ra:
        a_shape = "result"
    elif "error" in ra:
        a_shape = "error:%s" % ra["error"].get("code")
    elif ra.get("exited"):
        a_shape = "exit"
    else:
        a_shape = "silence"
    rec = {
        "cmd": cmd,
        "era": era,
        "discover_shape": a_shape,
        "discover_supported": sv,
        "discover_error": ra.get("error"),
        "initialize_version": (rb1.get("result") or {}).get("protocolVersion"),
        "initialize_error": rb1.get("error"),
        "legacy_tools_ok": "result" in rb2,
        "raw": {"discover": a, "legacy": b},
    }
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1, sort_keys=True)
    print(json.dumps({k: rec[k] for k in ("era", "discover_shape", "discover_supported", "initialize_version", "legacy_tools_ok")}))


if __name__ == "__main__":
    main()
