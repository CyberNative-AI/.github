"""Rerun secondary statistics on the O set, added after the run (score_fvep.py computed O BA without CIs).
usage: secondary_o.py out/score.json out/secondary_o.json
Reads the per-row predictions already in score.json; ba/boot/mcnemar/flips are copied verbatim from score_fvep.py."""
import json, math, random, sys

LABELS = ("pathogenic", "benign")

def ba(rows, key):
    rec = {}
    for lab in LABELS:
        sub = [r for r in rows if r["label"] == lab]
        rec[lab] = sum(r[key] == lab for r in sub) / len(sub) if sub else float("nan")
    return (rec["pathogenic"] + rec["benign"]) / 2, rec

def boot(rows, fn, n=2000, seed=18001):
    rng = random.Random(seed)
    P = [r for r in rows if r["label"] == "pathogenic"]
    B = [r for r in rows if r["label"] == "benign"]
    vals = sorted(fn([rng.choice(P) for _ in P] + [rng.choice(B) for _ in B]) for _ in range(n))
    return [round(vals[int(0.025 * n)], 4), round(vals[int(0.975 * n) - 1], 4)]

def mcnemar(rows, a, b):
    ca = [r[a] == r["label"] for r in rows]
    cb = [r[b] == r["label"] for r in rows]
    n10 = sum(x and not y for x, y in zip(ca, cb))
    n01 = sum(y and not x for x, y in zip(ca, cb))
    k, n = min(n10, n01), n10 + n01
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2**n) if n else 1.0
    return {f"{a}_right_{b}_wrong": n10, f"{b}_right_{a}_wrong": n01, "p_exact_two_sided": round(p, 6)}

def flips(rows, a, b):
    both = [r for r in rows if r[a] != "INVALID" and r[b] != "INVALID"]
    return {"n_both_valid": len(both), "label_changed": sum(r[a] != r[b] for r in both),
            "rate": round(sum(r[a] != r[b] for r in both) / len(both), 4) if both else None}

rows = [r for r in json.load(open(sys.argv[1]))["rows"] if r["set"] == "O"]
out = {"n": len(rows)}
for a in ("F_plus", "F_gene", "C_orig", "R"):
    out[a] = {"BA": round(ba(rows, a)[0], 4), "BA_CI95": boot(rows, lambda s, a=a: ba(s, a)[0])}
for a in ("F_plus", "F_gene"):
    out[a]["delta_vs_C_orig"] = round(out[a]["BA"] - out["C_orig"]["BA"], 4)
    out[a]["delta_vs_C_orig_CI95"] = boot(rows, lambda s, a=a: ba(s, a)[0] - ba(s, "C_orig")[0])
    out[a]["R_minus_arm_CI95"] = boot(rows, lambda s, a=a: ba(s, "R")[0] - ba(s, a)[0])
    out[a]["mcnemar_vs_C_orig"] = mcnemar(rows, a, "C_orig")
    out[a]["label_flips_vs_C_orig"] = flips(rows, a, "C_orig")
json.dump(out, open(sys.argv[2], "w"), indent=1, sort_keys=True)
print(json.dumps(out, indent=1, sort_keys=True))
