"""Score generator outputs. Usage: python3 score.py DIR LIVE_LIBRARY_FILE
DIR holds sim-YYYY-MM-DD-r1.txt and -r2.txt per date (as written by run-generator.sh)."""
import sys, re, json, glob, os
D, LIVE = sys.argv[1], sys.argv[2]
KEYS = ["lts", "lts-slim", "lts-alpine", "latest", "current", "slim", "alpine", "bookworm", "trixie", "current-alpine"]


def stanzas(t):
    out = []
    for b in t.split("\n\n"):
        m = re.search(r"^Tags: (.*)$", b, re.M)
        if not m:
            continue
        a = re.search(r"^Architectures: (.*)$", b, re.M); d = re.search(r"^Directory: (.*)$", b, re.M)
        out.append((tuple(x.strip() for x in m.group(1).split(",")), a.group(1).strip() if a else "", d.group(1).strip() if d else ""))
    return out


def tagmap(st):
    return {t: d for tags, _, d in st for t in tags}

live = stanzas(open(LIVE).read())
res = {"dates": {}}
base = None
for f in sorted(glob.glob(f"{D}/sim-*-r1.txt")):
    date = os.path.basename(f)[4:-7]
    t1, t2 = open(f).read(), open(f.replace("-r1.txt", "-r2.txt")).read()
    st = stanzas(t1); tm = tagmap(st)
    if date == "2026-10-22":
        base = set(tm)
        res["matches_live_20261022"] = sorted(st) == sorted(live)
    res["dates"][date] = {"repeat_identical": t1 == t2, "stanzas": len(st), "tags": len(tm),
                          "where": {k: tm.get(k) for k in KEYS}}
for date, v in res["dates"].items():
    tm = tagmap(stanzas(open(f"{D}/sim-{date}-r1.txt").read()))
    v["dropped_vs_20261022"] = sorted(base - set(tm)) if base else None
    v["latest_listed"] = "latest" in tm
print(json.dumps(res, indent=1))
