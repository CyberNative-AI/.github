"""Descriptive secondaries: precision proxy (fix-diff-addressed share of A2pre TOP10), non-static subset, hit rank distribution."""
import json, glob
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
GT = json.loads((ROOT / "GROUND_TRUTH.json").read_text())
key = json.loads((ROOT / "adjudication/units_key.json").read_text())
V = {}
for f in sorted(glob.glob(str(ROOT / "adjudication/verdicts_*.json"))): V.update(json.load(open(f)))
P = {}
for f in sorted(glob.glob(str(ROOT / "precision/out_*.json"))): P.update(json.load(open(f)))
gtrank = {u["case"]: V[u["uid"]].get("rank") if V[u["uid"]]["match"] else None for u in key if u["arm"] == "A2pre"}
addr = {c: sorted(set(int(x) for x in P[c] if 1 <= int(x) <= 10)) for c in GT}
tot = sum(len(v) for v in addr.values())
excl = sum(len([x for x in v if x != gtrank[c]]) for c, v in addr.items())
res = {"precision_proxy": {"cases": len(addr), "items": 800, "addressed_by_fix": tot, "share": round(tot / 800, 4),
       "addressed_excluding_gt_item": excl, "share_excl_gt": round(excl / 800, 4),
       "cases_with_any_addressed": sum(1 for v in addr.values() if v),
       "gt_hit_cases_where_fix_addresses_gt_rank": sum(1 for c, r in gtrank.items() if r and r in addr[c])}}
hit = {(u["arm"], u["case"]): V[u["uid"]]["match"] for u in key if not u["arm"].startswith("PC")}
NS = [c for c in GT if GT[c].get("static_detectable") != "yes"]
res["non_static_subset"] = {"n": len(NS), **{a: round(sum(hit[(a, c)] for c in NS) / len(NS), 4) for a in ("A2pre", "Npre", "A2post", "A0")}}
res["A2pre_hit_ranks"] = sorted(r for r in gtrank.values() if r)
(ROOT / "secondary.json").write_text(json.dumps(res, indent=1) + "\n"); print(json.dumps(res, indent=1))
