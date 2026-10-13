"""Post hoc (A02): split the recorder discover->initialize gap into server reply latency and client fallback latency,
and compare connect time of DUAL vs LEGACY clients on the same legacy server. Not part of the frozen rule."""
import json, os, statistics, sys
from collections import defaultdict
rd = sys.argv[1]
era = json.load(open(os.path.join(rd, "client_era.json")))["client_era"]
probes = {f[:-5]: json.load(open(os.path.join(rd, "probes", f)))["era"] for f in os.listdir(os.path.join(rd, "probes"))}
rows = defaultdict(list); conn = defaultdict(list)
for ln in open(os.path.join(rd, "cells.jsonl")):
    r = json.loads(ln)
    if r["tag"] != "main":
        continue
    res = r.get("result") or {}
    conn[(r["server"], era[r["client"]])].append(res.get("t_connect_ms"))
    p = os.path.join(rd, "tap", "%s__%s__%s__%d.jsonl" % (r["tag"], r["client"], r["server"], r["rep"]))
    ev = [json.loads(x) for x in open(p)]
    disc_id = t_disc = t_reply = t_init = t_first_s2c = None
    for e in ev:
        if e["dir"] not in ("c2s", "s2c"):
            continue
        try:
            m = json.loads(e["line"])
        except ValueError:
            continue
        if e["dir"] == "s2c" and t_first_s2c is None:
            t_first_s2c = e["t_ms"]
        if e["dir"] == "c2s" and m.get("method") == "server/discover" and t_disc is None:
            t_disc, disc_id = e["t_ms"], m.get("id")
        if e["dir"] == "s2c" and disc_id is not None and m.get("id") == disc_id and t_reply is None:
            t_reply = e["t_ms"]
        if e["dir"] == "c2s" and m.get("method") == "initialize" and t_init is None:
            t_init = e["t_ms"]
    if t_disc is not None and t_init is not None and t_reply is not None:
        rows[(r["client"], r["server"])].append((t_reply - t_disc, t_init - t_reply))
out = {"fallback_cells": [], "connect_by_server": {}}
for (c, s), v in sorted(rows.items()):
    out["fallback_cells"].append({"client": c, "server": s, "server_reply_ms_median": statistics.median(x[0] for x in v),
                                  "client_fallback_ms_median": statistics.median(x[1] for x in v), "client_fallback_ms_max": max(x[1] for x in v), "n": len(v)})
for (s, e), v in sorted(conn.items()):
    v = [x for x in v if x is not None]
    out["connect_by_server"].setdefault(s, {})[e] = {"median_ms": statistics.median(v), "n": len(v)}
json.dump(out, sys.stdout, indent=1, sort_keys=True)
