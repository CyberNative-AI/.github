"""Run the mcp-stdio-cross-era client x server matrix inside one container (stdlib only).

usage: python3 run_matrix.py CONFIG.json OUTDIR [--clients a,b] [--servers x,y] [--repeats N] [--tag T]

CONFIG.json: {"clients": {impl: [argv...]}, "servers": {impl: {"cmd": [argv...], "tool": str, "args": {...}, "expect": str-or-null}}}
Each cell launches: CLIENT_ARGV -- python3 /src/tap.py <tap log> -- SERVER_CMD, with MCP_TOOL/MCP_ARGS set.
Writes OUTDIR/cells.jsonl (one record per run, appended) and OUTDIR/tap/<client>__<server>__<rep>.jsonl.
Cell order is a seeded shuffle of (client, server, repeat) so slow cells do not cluster.
"""

import argparse
import hashlib
import json
import os
import random
import signal
import subprocess
import sys
import time

HARD_TIMEOUT_S = 45


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("outdir")
    ap.add_argument("--clients")
    ap.add_argument("--servers")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--seed", type=int, default=13340)
    ap.add_argument("--tag", default="main")
    ap.add_argument("--notap", action="store_true")
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8"))
    clients = sorted(cfg["clients"]) if not a.clients else a.clients.split(",")
    servers = sorted(cfg["servers"]) if not a.servers else a.servers.split(",")
    os.makedirs(os.path.join(a.outdir, "tap"), exist_ok=True)
    cells = [(c, s, r) for c in clients for s in servers for r in range(a.repeats)]
    random.Random(a.seed).shuffle(cells)
    out = open(os.path.join(a.outdir, "cells.jsonl"), "a", encoding="utf-8")
    for i, (c, s, r) in enumerate(cells):
        srv = cfg["servers"][s]
        tap = os.path.join(a.outdir, "tap", "%s__%s__%s__%d.jsonl" % (a.tag, c, s, r))
        if os.path.exists(tap):
            os.remove(tap)
        argv = list(cfg["clients"][c]) + ["--"] + ((["/usr/bin/python3", "/src/tap.py", tap, "--"]) if not a.notap else []) + list(srv["cmd"])
        env = dict(os.environ)
        env["MCP_TOOL"] = srv.get("tool", "echo")
        env["MCP_ARGS"] = json.dumps(srv.get("args", {"message": "hello-re13340"}))
        t0 = time.monotonic()
        rec = {"tag": a.tag, "client": c, "server": s, "rep": r, "argv": argv}
        p = subprocess.Popen(argv, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        try:
            so, se = p.communicate(timeout=HARD_TIMEOUT_S)
            rec["rc"] = p.returncode
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            so, se = p.communicate()
            rec["rc"] = None
            rec["hard_timeout"] = True
        try:
            os.killpg(p.pid, signal.SIGKILL)  # reap any server left behind by the client
            rec["leftover_group"] = True
        except ProcessLookupError:
            rec["leftover_group"] = False
        so = so.decode("utf-8", "replace")
        rec["stdout_tail"] = so[-4000:]
        rec["stderr_tail"] = se.decode("utf-8", "replace")[-2000:]
        lines = [ln for ln in so.splitlines() if ln.strip().startswith("{")]
        try:
            rec["result"] = json.loads(lines[-1]) if lines else None
        except ValueError:
            rec["result"] = None
        rec["wall_ms"] = round((time.monotonic() - t0) * 1000, 1)
        rec["expect"] = srv.get("expect")
        if os.path.exists(tap):
            rec["tap_sha256"] = hashlib.sha256(open(tap, "rb").read()).hexdigest()
        out.write(json.dumps(rec, sort_keys=True) + "\n")
        out.flush()
        res = rec.get("result") or {}
        print("%d/%d %s x %s r%d: conn=%s list=%s call=%s %sms %s" % (i + 1, len(cells), c, s, r, res.get("connect_ok"), res.get("list_ok"), res.get("call_ok"), rec["wall_ms"], (res.get("error_msg") or "")[:80]), flush=True)
    out.close()


if __name__ == "__main__":
    main()
