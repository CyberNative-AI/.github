"""make: write adjudication/spotcheck_sheet.md (40 seeded cells, >=15 adjudicator-yes, verdicts hidden).
score: compare adjudication/spotcheck_mine.json {cell_id: true/false} with adjudicator verdicts; Cohen's kappa + positive agreement."""
import json, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; ADJ = ROOT / "adjudication"
GT = {i["id"]: i for i in json.loads((ROOT / "GROUND_TRUTH.json").read_text())["items"]}
KEY = {u["uid"]: u for u in json.loads((ADJ / "units_key.json").read_text())}
V = {}
for f in sorted(ADJ.glob("verdicts_*.json")): V.update(json.loads(f.read_text()))
cells = [(uid, it) for uid in sorted(KEY) if KEY[uid]["arm"] != "control" and KEY[uid]["part"] != "narration" for it in sorted(GT)]
rng = random.Random(13683)
if sys.argv[1] == "make":
    yes = [c for c in cells if V[c[0]][c[1]]["match"]]; no = [c for c in cells if not V[c[0]][c[1]]["match"]]
    pick = rng.sample(yes, 16) + rng.sample(no, 24); rng.shuffle(pick)
    texts = {}
    for b in sorted(ADJ.glob("batch_*.md")):
        t = b.read_text()
        for uid in KEY:
            s = f"=== CRITIQUE {uid} START ===\n"
            if s in t: texts[uid] = t.split(s)[1].split(f"\n=== CRITIQUE {uid} END ===")[0]
    sel = [{"cell": f"S{n:02d}", "uid": u, "item": i} for n, (u, i) in enumerate(pick)]
    (ADJ / "spotcheck_cells.json").write_text(json.dumps(sel, indent=1) + "\n")
    out = []
    for s in sel:
        out.append(f"## {s['cell']} item {s['item']}: {GT[s['item']]['match']}\n\n{texts[s['uid']]}\n")
    (ADJ / "spotcheck_sheet.md").write_text("\n".join(out))
    print(len(sel), "cells")
else:
    sel = json.loads((ADJ / "spotcheck_cells.json").read_text()); mine = json.loads((ADJ / "spotcheck_mine.json").read_text())
    a = [bool(V[s["uid"]][s["item"]]["match"]) for s in sel]; b = [bool(mine[s["cell"]]) for s in sel]
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n; pe = pa * pb + (1 - pa) * (1 - pb)
    kappa = (po - pe) / (1 - pe); both = sum(x and y for x, y in zip(a, b))
    pos = 2 * both / (sum(a) + sum(b))
    dis = [(s["cell"], s["uid"], s["item"], x, y) for s, x, y in zip(sel, a, b) if x != y]
    res = {"n": n, "agreement": round(po, 3), "kappa": round(kappa, 3), "positive_agreement": round(pos, 3), "adj_yes": sum(a), "mine_yes": sum(b), "disagreements": dis,
           "pass": kappa >= 0.70 and pos >= 0.75}
    (ADJ / "spotcheck_result.json").write_text(json.dumps(res, indent=1) + "\n"); print(json.dumps(res, indent=1))
