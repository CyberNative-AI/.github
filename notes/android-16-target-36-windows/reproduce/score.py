"""Score the emulator cell files: readout per cell, device validity checks, and whether each change is confirmed. usage: score.py OUTDIR"""
import json, sys, glob, re, collections
out = sys.argv[1]; cells = []; meta = {}
def parse(s):
    return dict(re.findall(r'(\w+)=(\S+)', s)) if s else None
for f in [p for p in (out + "/cells-%s.jsonl" % d for d in ("P36", "T36", "P35", "T35")) if glob.glob(p)]:  # the interrupted first tablet run (cells-T36-run1.jsonl) is not scored
    for l in open(f):
        j = json.loads(l)
        if "landscape_rotation" in j or "invalid" in j: meta.setdefault(f.split("cells-")[1][:-6], {}).update(j); continue
        if j.get("rep") == 0: continue
        j["s"] = parse(j["start"]); j["a"] = parse(j["after"]); cells.append(j)
def ro(c):
    s, a = c["s"], c["a"]
    if not s: return {"missing": True}
    r = {"ori": s["ori"], "under": int(s["inset"]) > 0 and int(s["top"]) < int(s["inset"]), "fill": s["win"] == s["max"], "top": int(s["top"]), "inset": int(s["inset"]), "win": s["win"], "max": s["max"], "target": s["target"]}
    if a: r["recreate"] = int(a["creates"]) > int(s["creates"]); r["ori_after"] = a["ori"]
    return r
tab = collections.defaultdict(list)
for c in cells: tab[(c["device"], c["flavor"], c["arm"])].append(ro(c))
def all_(dev, fl, arm, pred):
    v = tab.get((dev, fl, arm), []); return len(v) == 2 and all((not x.get("missing")) and pred(x) for x in v)
valid = {}
for dev in sorted({c["device"] for c in cells}):
    kind = "phone" if dev.startswith("P") else "tablet"; g = {}
    if meta.get(dev, {}).get("landscape_rotation", -1) == -1 or "invalid" in meta.get(dev, {}): g["landscape"] = False
    if kind == "phone":
        g["E0_under_t35"] = all_(dev, "t35", "E0", lambda x: x["under"]); g["E0_under_t36"] = all_(dev, "t36", "E0", lambda x: x["under"])
        g["E2_never_under"] = all_(dev, "t35", "E2", lambda x: not x["under"]) and all_(dev, "t36", "E2", lambda x: not x["under"])
        g["O1_P_t35"] = all_(dev, "t35", "O1", lambda x: x["ori"] == "P"); g["O1_P_t36"] = all_(dev, "t36", "O1", lambda x: x["ori"] == "P")
    else:
        for fl in ("t35", "t36", "t36prop", "t36game"): g["OU_L_" + fl] = all_(dev, fl, "OU", lambda x: x["ori"] == "L")
        g["O1_P_t35"] = all_(dev, "t35", "O1", lambda x: x["ori"] == "P")
    valid[dev] = {"valid": all(g.values()), "gates": g}
E_conf = valid.get("P36", {}).get("valid") and all_("P36", "t36", "E1", lambda x: x["under"]) and all_("P36", "t35", "E1", lambda x: not x["under"])
O_conf = valid.get("T36", {}).get("valid") and any(all_("T36", "t36", a, lambda x: x["ori"] == "L") and all_("T36", "t35", a, lambda x: x["ori"] == "P") and all_("T36", "t36prop", a, lambda x: x["ori"] == "P") for a in ("O1", "O2"))
summary = {f"{d}|{fl}|{a}": v for (d, fl, a), v in sorted(tab.items())}
print(json.dumps({"meta": meta, "validity": valid, "E_confirmed": bool(E_conf), "O_confirmed": bool(O_conf), "cells": summary}, indent=1))
