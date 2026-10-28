"""Score the run: parse Carbon-X answers, compare with AlphaMissense (M) and the consequence rule (O).
usage: score.py frame.jsonl carbon_raw.jsonl out_score.json"""
import json, random, re, sys, collections
RULE_P = {"nonsense", "splice_donor_variant", "splice_acceptor_variant", "initiator_codon_variant", "stop_lost"}
FINAL_TAG = re.compile(r"<answer>\s*(benign|pathogenic)\s*</answer>\s*\Z", re.I)
FINAL_LINE = re.compile(r"(?:^|\n)\s*answer:\s*(benign|pathogenic)\s*[.]?\s*\Z", re.I)

def parse(text):
    """Only the model's own final verdict line counts: `Answer: <label>` (its observed format) or the publisher's
    `<answer><label></answer>` tag at the end. Anything else is INVALID (no prose fallback: negations mislead)."""
    if not text:
        return None
    t = text.strip()
    m = FINAL_TAG.search(t) or FINAL_LINE.search(t)
    return m.group(1).lower() if m else None

def ba(rows, key):
    rec = {}
    for lab in ("pathogenic", "benign"):
        sub = [r for r in rows if r["label"] == lab]
        rec[lab] = sum(r[key] == lab for r in sub) / len(sub) if sub else float("nan")
    return (rec["pathogenic"] + rec["benign"]) / 2, rec

def auroc(rows):
    pos = [r["am_score"] for r in rows if r["label"] == "pathogenic"]
    neg = [r["am_score"] for r in rows if r["label"] == "benign"]
    if not pos or not neg:
        return float("nan")
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))

def boot(rows, ka, kb, n=2000, seed=17301):
    rng = random.Random(seed)
    P = [r for r in rows if r["label"] == "pathogenic"]
    B = [r for r in rows if r["label"] == "benign"]
    ds = []
    for _ in range(n):
        s = [rng.choice(P) for _ in P] + [rng.choice(B) for _ in B]  # stratified: keeps the class balance
        ds.append(ba(s, ka)[0] - ba(s, kb)[0])
    ds.sort()
    return ds[int(0.025 * n)], ds[int(0.975 * n) - 1]

frame = {json.loads(l)["id"]: json.loads(l) for l in open(sys.argv[1])}
MISSING = 0
raw = {}
for l in open(sys.argv[2]):
    x = json.loads(l)
    raw[x["id"]] = x  # last record wins (resumed runs append)
rows = []
for vid, r in frame.items():
    x = raw.get(vid)
    if x is None:
        MISSING += 1
        x = {"answer": None, "error": "MISSING", "finish_reason": None}
    pred = parse(x["answer"]) if x.get("error") is None and x.get("finish_reason") == "stop" else None
    row = {k: r.get(k) for k in ("id", "label", "stratum", "gene_symbol", "mc_terms", "am_score", "am_classes", "first_window_end", "oriented", "revstat")}
    row["missing"] = x.get("error") == "MISSING"
    row["C"] = pred or "INVALID"
    if r.get("am_score") is not None:
        row["A_bin"] = "pathogenic" if r["am_score"] > 0.5 else "benign"
        cls = r["am_classes"]
        row["A_cls"] = ("pathogenic" if cls == ["likely_pathogenic"] else "benign" if cls == ["likely_benign"] else "ABSTAIN")
    if r["mc_terms"] and len(r["mc_terms"]) == 1:
        row["R"] = "pathogenic" if r["mc_terms"][0] in RULE_P else "benign"
    rows.append(row)
res = {"n_frame": len(frame), "n_scored": len(rows), "n_missing_counted_invalid": MISSING}
M = [r for r in rows if r["stratum"].startswith("M|")]
O = [r for r in rows if r["stratum"].startswith("O|")]
S = [r for r in rows if r["stratum"].startswith("STRICT")]
def block(rs, arms):
    out = {"n": len(rs), "labels": dict(collections.Counter(r["label"] for r in rs)),
           "C_invalid": sum(r["C"] == "INVALID" for r in rs),
           "C_pred_rate": dict(collections.Counter(r["C"] for r in rs))}
    for a in arms:
        if all(a in r for r in rs) and rs:
            b, rec = ba(rs, a)
            out[f"BA_{a}"] = round(b, 4)
            out[f"recall_{a}"] = {k: round(v, 4) for k, v in rec.items()}
    return out
res["M"] = block(M, ["C", "A_bin"])
if M:
    res["M"]["D_Abin_minus_C"] = round(res["M"]["BA_A_bin"] - res["M"]["BA_C"], 4)
    lo, hi = boot(M, "A_bin", "C")
    res["M"]["D_CI95"] = [round(lo, 4), round(hi, 4)]
    res["M"]["AUROC_A"] = round(auroc(M), 4)
    res["M"]["C_invalid_rate"] = round(res["M"]["C_invalid"] / len(M), 4)
    amb = [r for r in M if r["A_cls"] == "ABSTAIN"]
    res["M_A_ambiguous"] = block(amb, ["C"])
    nonamb = [r for r in M if r["A_cls"] != "ABSTAIN"]
    res["M_A_cls_nonabstain"] = block(nonamb, ["C", "A_cls"])
    for g in ("W0905_0928", "W1019"):
        res[f"M_{g}"] = block([r for r in M if r["stratum"] == f"M|{g}"], ["C", "A_bin"])
    top = collections.Counter(r["gene_symbol"] for r in M).most_common(1)[0][0]
    res["M_leave_top_gene_out"] = dict(block([r for r in M if r["gene_symbol"] != top], ["C", "A_bin"]), top_gene=top)
    for o in ("plus", "minus"):
        res[f"M_strand_{o}"] = block([r for r in M if r["oriented"] == o], ["C", "A_bin"])
    two = [r for r in M if r["revstat"] != "criteria_provided,_single_submitter"]
    res["M_2plus_star"] = block(two, ["C", "A_bin"])
res["O"] = block(O, ["C", "R"])
for g in ("W0905_0928", "W1019"):
    res[f"O_{g}"] = block([r for r in O if r["stratum"] == f"O|{g}"], ["C", "R"])
res["STRICT"] = block(S, ["C"])  # 41P+3B: read pathogenic recall only (benign n=3 cannot support BA)
CT = [r for r in rows if r["stratum"].startswith("CTRL")]
res["CTRL"] = block(CT, ["C", "A_bin"])
res["STRICT_missense_with_A"] = block([r for r in S if r.get("am_score") is not None and r["mc_terms"] == ["missense_variant"]], ["C", "A_bin"])
d, lo = res["M"].get("D_Abin_minus_C"), res["M"].get("D_CI95", [None, None])
verdict = None
if M:
    if any(r["missing"] for r in M):
        verdict = "INCOMPLETE"
    elif res["M"]["C_invalid_rate"] > 0.10:
        verdict = "INVALID"
    elif d >= 0.10 and lo[0] > 0:
        verdict = "STOP"
    elif lo[1] < 0.05:
        verdict = "CONTINUE"
    else:
        verdict = "CHANGE"
res["verdict_rule"] = verdict
json.dump({"result": res, "rows": rows}, open(sys.argv[3], "w"), indent=1, sort_keys=True)
print(json.dumps(res, indent=1, sort_keys=True))
