"""Score A40 vs A41 per the outcome rules in ../README.md. Reads work/<arm>/res/<gem>/."""
import json, pathlib, re, sys
W = pathlib.Path("work")
removed = {l.strip() for l in open("data/removed.txt") if l.strip()} | {"rb_iterate"}
rank = {json.loads(l)["name"]: json.loads(l)["rank"] for l in open("data/frame.jsonl")}
def arm(a, g):
    d = W / a / "res" / g
    if not (d / "install.rc").exists(): return None
    rc = int((d / "install.rc").read_text().strip() or 99)
    loads = [l.split("\t", 1) for l in (d / "load.tsv").read_text().splitlines() if "\t" in l]
    loaded = [r for r, o in loads if "LOADED" in o]
    undef = {l.split("\t")[1] for l in (d / "undef.txt").read_text().splitlines() if "\t" in l}
    log = (d / "install.log").read_text(errors="replace")
    return {"rc": rc, "loaded": loaded, "load_out": loads, "undef_removed": sorted(undef & removed),
            "secs": int((d / "install.secs").read_text().strip() or 0), "log": log}
def cause(x, name):
    txt = x["log"] + " ".join(o for _, o in x["load_out"])
    hit = sorted({i for i in removed if re.search(r"\b%s\b" % re.escape(i), txt)} | set(x["undef_removed"]))
    if hit: return "REMOVED_API", hit
    m = re.findall(r"Gem files will remain installed in \S*/gems/([^/\s]+?) for inspection", x["log"])
    if m and not any(s.startswith(name + "-") for s in m): return "DEP", m
    return "OTHER", []
rows = []
for d in sorted((W / "A40" / "res").iterdir()):
    g = d.name; name = g.rsplit("-", 1)[0]
    a, b = arm("A40", g), arm("A41", g)
    if a is None or b is None: rows.append({"gem": g, "outcome": "MISSING"}); continue
    noreq = not a["loaded"] and not b["loaded"]
    ok40 = a["rc"] == 0 and (bool(a["loaded"]) or noreq)
    if a["rc"] == 124 or b["rc"] == 124: out = "TIMEOUT"
    elif not ok40: out = "ENV"
    elif b["rc"] != 0 or (a["loaded"] and not b["loaded"]) or b["undef_removed"]: out = "BREAK"
    else: out = "OK"
    r = {"gem": g, "name": name, "rank": rank.get(name), "outcome": out, "rc40": a["rc"], "rc41": b["rc"],
         "loaded40": a["loaded"], "loaded41": b["loaded"], "undef41": b["undef_removed"], "noreq": noreq,
         "secs40": a["secs"], "secs41": b["secs"]}
    if out == "BREAK": r["cause"], r["cause_ids"] = cause(b, name)
    rows.append(r)
json.dump(rows, open("data/score.json", "w"), indent=1)
from collections import Counter
ctl = [r for r in rows if r["gem"].startswith("cyba_")]
frame = [r for r in rows if not r["gem"].startswith("cyba_")]
print("controls:", [(r["gem"], r["outcome"]) for r in ctl])
print("frame", len(frame), Counter(r["outcome"] for r in frame))
print("top1000", Counter(r["outcome"] for r in frame if r.get("rank") and r["rank"] <= 1000))
for r in frame:
    if r["outcome"] in ("BREAK", "ENV", "TIMEOUT", "MISSING"):
        print(r["outcome"], r.get("rank"), r["gem"], r.get("cause"), r.get("cause_ids"), "rc", r.get("rc40"), r.get("rc41"), "noreq" if r.get("noreq") else "")
