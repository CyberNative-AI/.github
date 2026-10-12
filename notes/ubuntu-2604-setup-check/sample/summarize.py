"""Summarize results.jsonl by stratum: eligible repos (>=1 resolved or unresolved setup-python/ruby step on hosted ubuntu-latest), repos with BREAK."""
import collections, json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
strat = {}
for line in open(os.path.join(here, "repos.tsv")):
    if not line.startswith("#"):
        s, name = line.split("\t")[:2]
        strat[name.replace("/", "__")] = s
rows = [json.loads(l) for l in open(os.path.join(here, "results.jsonl"))]
agg = collections.defaultdict(collections.Counter)
reasons = collections.Counter(); specs = collections.Counter(); unk = collections.Counter()
for r in rows:
    key = os.path.basename(os.path.normpath(r["repo"])); s = strat[key]
    f = r["findings"]
    st = {x["status"] for x in f}
    rel = [x for x in f if x["status"] in ("OK", "BREAK", "ALREADY", "UNKNOWN") and (x["action"] or x["status"] == "UNKNOWN")]
    for t in ("all", s[:2], s):
        agg[t]["repos"] += 1
        if rel: agg[t]["eligible"] += 1
        if "BREAK" in st: agg[t]["break"] += 1
        if any(x["status"] == "BREAK" and not x["continueOnError"] for x in f): agg[t]["break_blocking"] += 1
        if rel and st & {"OK", "BREAK", "ALREADY"} == set() : agg[t]["only_unknown"] += 1
        if "UNKNOWN" in st: agg[t]["any_unknown"] += 1
    for x in f:
        if x["status"] == "BREAK":
            specs[(x["action"], x["spec"])] += 1
            src = x["where"].split(": ", 1)[1].split(":")[0] if ": " in x["where"] else "?"
            reasons[(x["action"], "file" if src not in ("python-version", "ruby-version") else "input")] += 1
        if x["status"] == "UNKNOWN":
            unk[x["where"].split(": ", 1)[-1][:40]] += 1
print("stratum      repos eligible break break_blocking any_unknown only_unknown  break/eligible")
for t in ("all", "py", "py-mid", "py-top", "rb", "rb-mid", "rb-top"):
    a = agg[t]
    pct = 100 * a["break"] / a["eligible"] if a["eligible"] else 0
    print(f"{t:10} {a['repos']:6} {a['eligible']:8} {a['break']:5} {a['break_blocking']:14} {a['any_unknown']:11} {a['only_unknown']:12}  {pct:5.1f}%")
print("\nBREAK steps by action/source:", dict(reasons))
print("top BREAK specs:", specs.most_common(25))
print("top UNKNOWN reasons:", unk.most_common(15))
