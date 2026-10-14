"""Compute frozen metrics and ruling from adjudication/verdicts_*.json (+ optional adjudication/override.json)."""
import json, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
GT = json.loads((ROOT / "GROUND_TRUTH.json").read_text())
key = {u["uid"]: u for u in json.loads((ROOT / "adjudication/units_key.json").read_text())}
V = {}
for f in sorted((ROOT / "adjudication").glob("verdicts_*.json")): V.update(json.loads(f.read_text()))
ov = ROOT / "adjudication/override.json"
if ov.exists(): V.update(json.loads(ov.read_text()))
miss = [u for u in key if u not in V]
if miss: raise SystemExit(f"unjudged units: {len(miss)}")
cases = sorted(GT)
hit, rank = {}, {}
for uid, u in key.items():
    if u["arm"].startswith("PC"): continue
    hit[(u["arm"], u["case"])] = bool(V[uid]["match"]); rank[(u["arm"], u["case"])] = V[uid].get("rank")
ARMS = ["A2pre", "Npre", "A2post", "A0"]
units_missing = sum(1 for a in ARMS for c in cases if (a, c) not in hit)
def h(arm, cs, k=10):
    return sum(1 for c in cs if hit.get((arm, c)) and (rank.get((arm, c)) or 99) <= k) / len(cs)
def boot(f, cs, n=10000):
    rng = random.Random(13683); vals = sorted(f([cs[rng.randrange(len(cs))] for _ in cs]) for _ in range(n))
    return [round(vals[int(0.025 * n)], 4), round(vals[int(0.975 * n) - 1], 4)]
# unit missing from an arm counts as no hit (conservative for the arm)
res = {"n_cases": len(cases), "units_missing": units_missing}
for a in ARMS:
    res[f"hit_{a}"] = round(h(a, cases), 4); res[f"hit_{a}_ci"] = boot(lambda cs, a=a: h(a, cs), cases)
    res[f"hit5_{a}"] = round(h(a, cases, 5), 4)
res["L_f"] = round(h("A2pre", cases) - h("A0", cases), 4); res["L_f_ci"] = boot(lambda cs: h("A2pre", cs) - h("A0", cs), cases)
res["L_p"] = round(h("A2pre", cases) - h("A2post", cases), 4); res["L_p_ci"] = boot(lambda cs: h("A2pre", cs) - h("A2post", cs), cases)
res["N_minus_A2"] = round(h("Npre", cases) - h("A2pre", cases), 4); res["N_minus_A2_ci"] = boot(lambda cs: h("Npre", cs) - h("A2pre", cs), cases)
res["union_A2_N"] = round(sum(1 for c in cases if hit.get(("A2pre", c)) or hit.get(("Npre", c))) / len(cases), 4)
for kind in ("mechanical", "conceptual"):
    cs = [c for c in cases if GT[c]["kind"] == kind]
    res[f"by_kind_{kind}"] = {"n": len(cs), **{a: round(h(a, cs), 4) for a in ARMS}} if cs else {"n": 0}
S = [c for c in cases if GT[c].get("static_detectable") == "yes"]
res["static_subset"] = {"n": len(S), **{a: round(h(a, S), 4) for a in ARMS}, "L_f": round(h("A2pre", S) - h("A0", S), 4),
    "L_f_ci": boot(lambda cs: h("A2pre", cs) - h("A0", cs), S), "L_p": round(h("A2pre", S) - h("A2post", S), 4),
    "L_p_ci": boot(lambda cs: h("A2pre", cs) - h("A2post", cs), S), "hit_A2pre_ci": boot(lambda cs: h("A2pre", cs), S)} if S else {"n": 0}
cont = {(a, c) for a in ("A2pre", "A2post") for c in cases}
res["pre_post_table"] = {f"{x}{y}": sum(1 for c in cases if hit.get(("A2pre", c)) == x and hit.get(("A2post", c)) == y) for x in (True, False) for y in (True, False)}
pcs = {uid: (u["arm"], u["case"], V[uid]) for uid, u in key.items() if u["arm"].startswith("PC")}
pos = [v["match"] for a, c, v in pcs.values() if a == "PCpos"]; neg = [v["match"] for a, c, v in pcs.values() if a == "PCneg"]
res["controls"] = {"pos_found": sum(pos), "pos_n": len(pos), "neg_fp": sum(neg), "neg_n": len(neg), "pass": sum(pos) >= 3 and sum(neg) <= 1}
hp, lf, lp = res["hit_A2pre"], res["L_f"], res["L_p"]
if res["n_cases"] < 40 or not res["controls"]["pass"] or units_missing > 0.10 * 4 * len(cases):
    ruling = "INVALID"
elif hp >= 0.35 and lf >= 0.15 and lp >= 0.10:
    ruling = "CONTINUE"
    spans = [res["hit_A2pre_ci"][0] < 0.35, res["L_f_ci"][0] < 0.15, res["L_p_ci"][0] < 0.10]
    if any(spans): ruling = "CHANGE (borderline)"
elif hp < 0.20 or lf < 0.05 or lp < 0.03:
    ruling = "STOP"
    deciding = [(hp < 0.20, res["hit_A2pre_ci"][1] >= 0.20), (lf < 0.05, res["L_f_ci"][1] >= 0.05), (lp < 0.03, res["L_p_ci"][1] >= 0.03)]
    if all(span for trig, span in deciding if trig): ruling = "CHANGE (borderline)"
else:
    ruling = "CHANGE"
res["ruling"] = ruling
res["N_recommend_over_A2"] = res["N_minus_A2"] >= 0.10 and res["N_minus_A2_ci"][0] > 0
(ROOT / "results.json").write_text(json.dumps(res, indent=1) + "\n")
print(json.dumps(res, indent=1))
