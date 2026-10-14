"""Score the experiment from adjudication/verdicts_*.json (+ optional adjudication/override.json). Writes results.json; prints summary."""
import json, random, re, statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GT = json.loads((ROOT / "GROUND_TRUTH.json").read_text())
KEY = {u["uid"]: u for u in json.loads((ROOT / "adjudication/units_key.json").read_text())}
CK = json.loads((ROOT / "controls/KEYS.json").read_text())
V = {}
for f in sorted((ROOT / "adjudication").glob("verdicts_*.json")):
    V.update(json.loads(f.read_text()))
ov = ROOT / "adjudication/override.json"
if ov.exists():
    for uid, items in json.loads(ov.read_text()).items():
        for it, m in items.items():
            V[uid][it]["match"] = m
missing = sorted(set(KEY) - set(V))
assert not missing, f"no verdicts for {missing}"
ITEMS = [i["id"] for i in GT["items"]]
H = [i for i in ITEMS if i.startswith("H")]; C = [i for i in ITEMS if i.startswith("C")]
FIX = {i["id"]: i["fixed_in_post"] for i in GT["items"]}
for uid in KEY:
    for it in ITEMS + ["R01"]:
        assert it in V[uid], (uid, it)
def m(uid, it): return bool(V[uid][it]["match"])

out = {}
# positive controls
pcs = {}
for uid, u in KEY.items():
    if u["arm"] != "control": continue
    k = CK[u["version"]]; yes = set(k["yes"]); either = set(k["either"]); planted = set(k["planted"])
    found = sorted(i for i in ITEMS if m(uid, i))
    fp = sorted(i for i in found if i not in yes and i not in either)
    sens = sum(i in found for i in planted)
    pcs[u["version"]] = {"found": found, "planted_found": f"{sens}/{len(planted)}", "fp": fp,
                         "pass": (sens >= len(planted) - 1 if planted else True) and len(fp) <= 1}
out["controls"] = pcs

# per-run scored sets
runs = {}
for uid, u in KEY.items():
    if u["arm"] == "control": continue
    r = runs.setdefault((u["arm"], u["version"], u["run"]), {})
    r[u["part"]] = {i for i in ITEMS + ["R01"] if m(uid, i)}
def scored(arm, part="primary"):
    res = {}
    for (a, v, k), parts in runs.items():
        if a != arm: continue
        s = parts.get("problems", parts.get("list"))
        if part == "with_narration" and "narration" in parts: s = s | parts["narration"]
        res.setdefault(v, []).append(s)
    return res
rng = random.Random(13683)
def boot(vals, n=10000):
    if len(vals) < 2: return [None, None]
    ms = sorted(st.mean(rng.choices(vals, k=len(vals))) for _ in range(n))
    return [round(ms[int(0.025 * n)], 3), round(ms[int(0.975 * n) - 1], 3)]
def recall(sets, items): return [len(s & set(items)) / len(items) for s in sets]
summary = {}
for arm in ("A2_simulated", "A1_generic", "A0_nodoc"):
    for part in (("primary", "with_narration") if arm == "A2_simulated" else ("primary",)):
        for v, sets in scored(arm, part).items():
            rH = recall(sets, H); rH7 = recall(sets, [i for i in H if i != "H07"]); rHt = recall(sets, [i for i in H if i != "H11"])
            rC = recall(sets, C)
            summary[f"{arm}|{v}|{part}"] = {"n": len(sets), "recall_H_mean": round(st.mean(rH), 3), "recall_H_ci": boot(rH),
                "recall_H_runs": [round(x, 3) for x in rH], "recall_H_noH07": round(st.mean(rH7), 3), "recall_H_textdet": round(st.mean(rHt), 3),
                "recall_C_mean": round(st.mean(rC), 3), "union_H": sorted(set().union(*sets) & set(H)), "union_C": sorted(set().union(*sets) & set(C)),
                "rate": {i: sum(i in s for s in sets) for i in ITEMS + ["R01"]}}
out["summary"] = summary

# discrimination on A2 primary
pre, post = scored("A2_simulated")["pre"], scored("A2_simulated")["post"]
def disc(pre, post):
    rate = lambda sets, i: sum(i in s for s in sets) / len(sets)
    elig = [i for i in ITEMS if sum(i in s for s in pre) >= 2]
    fx = [i for i in elig if FIX[i] == "yes"]; ux = [i for i in elig if FIX[i] == "no"]
    d = lambda its: st.mean(rate(pre, i) - rate(post, i) for i in its) if its else None
    if len(fx) >= 4 and len(ux) >= 2: return {"ND": d(fx) - d(ux), "D_fixed": d(fx), "D_unfixed": d(ux), "label": "controlled", "fixed": fx, "unfixed": ux}
    if len(fx) >= 4: return {"ND": d(fx), "D_fixed": d(fx), "D_unfixed": d(ux), "label": "uncontrolled", "fixed": fx, "unfixed": ux}
    return {"ND": None, "label": "not estimable", "fixed": fx, "unfixed": ux}
D = disc(pre, post)
if D["ND"] is not None:
    bs = []
    for _ in range(10000):
        bp, bq = rng.choices(pre, k=len(pre)), rng.choices(post, k=len(post))
        rate = lambda sets, i: sum(i in s for s in sets) / len(sets)
        dd = lambda its: st.mean(rate(bp, i) - rate(bq, i) for i in its) if its else 0.0
        bs.append(dd(D["fixed"]) - (dd(D["unfixed"]) if D["label"] == "controlled" else 0.0))
    bs.sort(); D["ND_ci"] = [round(bs[250], 3), round(bs[9749], 3)]
    D["ND"] = round(D["ND"], 3)
out["discrimination"] = D
out["partial_items_rates"] = {i: [sum(i in s for s in pre), sum(i in s for s in post)] for i in ITEMS if FIX[i] == "partial"}

# never found in A1+A2 pre
pre_all = scored("A2_simulated")["pre"] + scored("A1_generic")["pre"]
out["never_found_pre"] = [i for i in ITEMS if not any(i in s for s in pre_all)]
# volume
def count_items(text): return len(re.findall(r"^\s*\d+[.)]\s", text, flags=re.M))
vol = {}
for f in sorted((ROOT / "runs").glob("*.md")):
    arm, v, k = f.stem.split("__"); t = f.read_text()
    if arm == "A2_simulated": t = re.split(r"^[#*\s]*PROBLEMS\b.*$", t, flags=re.M | re.I)[-1]
    vol.setdefault(f"{arm}|{v}", []).append(count_items(t))
out["volume"] = vol
# yes-rate by version
yr = {}
for uid, u in KEY.items():
    if u["arm"] == "control": continue
    yr.setdefault(u["version"], []).append(sum(m(uid, i) for i in ITEMS))
out["yes_per_unit_by_version"] = {v: round(st.mean(x), 2) for v, x in yr.items()}

# ruling
a2 = summary["A2_simulated|pre|primary"]; a0 = summary["A0_nodoc|none|primary"]
rec, ci = a2["recall_H_mean"], a2["recall_H_ci"]; floor = round(rec - a0["recall_H_mean"], 3)
nd = D["ND"]
pc_ok = all(p["pass"] for p in pcs.values())
if not pc_ok: ruling = "ADJUDICATION FAILED POSITIVE CONTROL (re-brief per protocol)"
elif rec < 0.30 or floor < 0.10 or (nd is not None and nd < 0.10): ruling = "STOP"
elif rec >= 0.50 and floor >= 0.20 and (nd is None or nd >= 0.25): ruling = "CONTINUE"
else: ruling = "CHANGE"
border = []
if ruling == "STOP":
    if rec < 0.30 and ci[1] is not None and ci[1] >= 0.30 and not (floor < 0.10) and not (nd is not None and nd < 0.10): border.append("recall CI spans 0.30")
    if nd is not None and nd < 0.10 and D.get("ND_ci", [0, 0])[1] >= 0.10 and not (rec < 0.30) and not (floor < 0.10): border.append("ND CI spans 0.10")
if ruling == "CONTINUE":
    if ci[0] is not None and ci[0] < 0.50: border.append("recall CI spans 0.50")
    if nd is not None and D["ND_ci"][0] < 0.25: border.append("ND CI spans 0.25")
if border: ruling = f"CHANGE (borderline: {'; '.join(border)}; frozen-rule point ruling {ruling})"
out["ruling"] = {"ruling": ruling, "recall_H_A2pre": rec, "recall_H_ci": ci, "floor_adjusted": floor, "A0_recall_H": a0["recall_H_mean"], "ND": nd, "ND_label": D["label"]}
(ROOT / "results.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(out["ruling"], indent=1)); print(json.dumps(out["controls"], indent=1))
