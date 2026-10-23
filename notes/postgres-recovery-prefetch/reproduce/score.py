"""Scorer: per-run metrics + validity gates + per-cell ruling. Reads a copy of the results folder."""
import json, os, re, statistics, sys, pathlib
ROOT = pathlib.Path(sys.argv[1])          # readable copy of /work (runs + gen.json)
DEV = os.environ.get("DEV", "8:32")  # major:minor of the disk under test (ours: 8:32)
def iostat(p):
    for l in p.read_text().splitlines():
        f = l.split()
        if f and f[0] == DEV:
            return {k: int(v) for k, v in (x.split("=") for x in f[1:])}
    return {"rbytes": 0, "rios": 0, "wbytes": 0, "wios": 0}
rows, cells = [], {}
for gen in sorted(ROOT.glob("*/gen.json")):
    tag = gen.parent.name
    if tag.startswith("pilot"): continue
    g = json.loads(gen.read_text())
    for rd in sorted((gen.parent / "runs").glob("*")):
        rj = rd / "run.json"
        if not rj.exists(): continue
        r = json.loads(rj.read_text()); log = (rd / "pg.log").read_text(errors="replace")
        m = re.search(r"redo done at \S+ system usage: CPU: user: ([\d.]+) s, system: ([\d.]+) s, elapsed: ([\d.]+) s", log)
        a, b = iostat(rd / "io0"), iostat(rd / "io1")
        d = {k: b.get(k, 0) - a.get(k, 0) for k in ("rbytes", "rios", "wbytes", "wios")}
        pf = (rd / "prefetch_final.csv").read_text().strip().split(",") if (rd / "prefetch_final.csv").exists() else []
        pfn = [int(x) for x in pf] if len(pf) == 6 else None
        gates = {"redo_logged": bool(m), "ready": r["done"] == 1,
                 "cold": d["rbytes"] >= 0.9 * g["update_wal_bytes"],
                 "setting_took_effect": (pfn is not None) and ((sum(pfn) == 0) if r["pf"] == "off" else (sum(pfn) > 0))}
        row = {"tag": tag, "pf": r["pf"], "rep": r["rep"], "redo_s": float(m.group(3)) if m else None,
               "redo_cpu_user_s": float(m.group(1)) if m else None, "redo_cpu_sys_s": float(m.group(2)) if m else None,
               "wall_s": round(r["t1"] - r["t0"], 1), **{"dev_" + k: v for k, v in d.items()},
               "kb_per_read_io": round(d["rbytes"] / d["rios"] / 1024, 1) if d["rios"] else None,
               "prefetch_final": dict(zip(["prefetch", "hit", "skip_init", "skip_new", "skip_fpw", "skip_rep"], pfn)) if pfn else None,
               "update_wal_bytes": g["update_wal_bytes"], "gates": gates, "valid": all(gates.values())}
        rows.append(row); cells.setdefault(tag, []).append(row)
def arm(x):
    pre = re.sub(r"\d+$", "", str(x["rep"]))
    return {"": "deb", "pv": "vsrc", "pp": "psrc", "c": "deb_cap300", "cp": "psrc_cap300",
            "w": "deb", "wp": "psrc", "wv": "vsrc"}[pre] + ":" + x["pf"]
for x in rows: x["arm"] = arm(x)
def med(tag, a):
    v = [x["redo_s"] for x in rows if x["tag"] == tag and x["arm"] == a and x["valid"]]
    return v
def ruling(t, o):
    if not t or not o: return "INCOMPLETE"
    R = statistics.median(t) / statistics.median(o)
    if R > 1.25 and min(t) > max(o): return "HARMFUL"
    if R < 0.8 and max(t) < min(o): return "HELPFUL"
    return "NO_EFFECT_OR_MIXED"
summary = {}
for tag in sorted({x["tag"] for x in rows}):
    arms = sorted({x["arm"] for x in rows if x["tag"] == tag})
    d = {a: {"redo_s": med(tag, a),
             "read_ios": [x["dev_rios"] for x in rows if x["tag"] == tag and x["arm"] == a and x["valid"]],
             "read_MB": [round(x["dev_rbytes"]/1e6) for x in rows if x["tag"] == tag and x["arm"] == a and x["valid"]],
             "prefetch": [x["prefetch_final"]["prefetch"] for x in rows if x["tag"] == tag and x["arm"] == a and x["valid"] and x["prefetch_final"]]}
         for a in arms}
    d["n_invalid"] = sum(1 for x in rows if x["tag"] == tag and not x["valid"])
    for base in ("deb", "deb_cap300"):
        t, o = med(tag, base + ":try"), med(tag, base + ":off")
        if t and o:
            d["ruling_" + base] = ruling(t, o); d["R_" + base] = round(statistics.median(t) / statistics.median(o), 3)
    summary[tag] = d
json.dump({"runs": rows, "cells": summary}, sys.stdout, indent=1)
