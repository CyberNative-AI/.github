"""POST HOC counts: references presence by VTEC action and messageType; segment-root share. Writes out/posthoc_counts.json."""
import collections, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); import analyze as A
alerts, _ = A.load(Path(sys.argv[1]))
t = collections.Counter()
for a in alerts:
    if a.get("_extra"): continue
    for s in (a.get("parameters") or {}).get("VTEC") or []:
        v = A.parse_vtec(s)
        if v and v["k"] == "O":
            t[(v["action"], a["messageType"], "has_refs" if A.ref_ids(a) else "no_refs")] += 1
out = {"|".join(k): n for k, n in sorted(t.items())}
Path(sys.argv[2]).write_text(json.dumps(out, indent=1) + "\n"); print(json.dumps(out, indent=1))
