"""Score the rerun. usage: score_fvep.py FIRST_RUN_DIR fvep_raw.jsonl fvep_ctrl_raw.jsonl tokcheck.json out_score.json
Parser for the FrontierVEP arms = the publisher's vepqa.py scorer: the completion must END with <answer>[^<]*</answer>
(trailing whitespace allowed); the tag text, stripped and casefolded, must be exactly benign or pathogenic. Also INVALID:
finish_reason != stop, request error, missing record. INVALID counts as wrong (vepqa.py counts it in the BA denominators).
The first run's own answers (C_orig) are re-parsed with its frozen parser (copied verbatim)."""
import collections, json, math, random, re, sys
R, RAW, CRAW, TOK, OUT = sys.argv[1:6]
VEPQA_FINAL = re.compile(r"(<answer>[^<]*</answer>)\s*\Z", re.DOTALL)  # vepqa.py _FINAL_ANSWER_PATTERN
# ../src/score.py, verbatim
FINAL_TAG = re.compile(r"<answer>\s*(benign|pathogenic)\s*</answer>\s*\Z", re.I)
FINAL_LINE = re.compile(r"(?:^|\n)\s*answer:\s*(benign|pathogenic)\s*[.]?\s*\Z", re.I)
RULE_P = {"nonsense", "splice_donor_variant", "splice_acceptor_variant", "initiator_codon_variant", "stop_lost"}
LABELS = ("benign", "pathogenic")

def parse_vepqa(text):
    m = VEPQA_FINAL.search(text or "")
    if not m:
        return None
    a = m.group(1).removeprefix("<answer>").removesuffix("</answer>").strip().casefold()
    return a if a in LABELS else None

def parse_17301(text):
    if not text:
        return None
    m = FINAL_TAG.search(text.strip()) or FINAL_LINE.search(text.strip())
    return m.group(1).lower() if m else None

def invalid_shape(x):
    if x is None:
        return "missing"
    if x.get("error"):
        return "error"
    if x.get("finish_reason") != "stop":
        return "not_stop:" + str(x.get("finish_reason"))
    t = x.get("answer") or ""
    m = VEPQA_FINAL.search(t)
    if m:
        return "final_tag_other_text:" + m.group(1)[:40]
    if "<answer>" in t:
        return "tag_not_final"
    if re.search(r"(?:^|\n)\s*answer:\s*\S", t, re.I):
        return "answer_line_no_tag"
    return "no_tag"

def pred(x, parser):
    if x is None or x.get("error") or x.get("finish_reason") != "stop":  # callers treat error records as missing
        return None
    return parser(x.get("answer"))

def ba(rows, key):
    rec = {}
    for lab in LABELS:
        sub = [r for r in rows if r["label"] == lab]
        rec[lab] = sum(r[key] == lab for r in sub) / len(sub) if sub else float("nan")
    return (rec["pathogenic"] + rec["benign"]) / 2, rec

def boot(rows, fn, n=2000, seed=18001):
    """Label-stratified bootstrap over variants (keeps 150/150); paired when fn compares two arms on the same rows."""
    rng = random.Random(seed)
    P = [r for r in rows if r["label"] == "pathogenic"]
    B = [r for r in rows if r["label"] == "benign"]
    vals = sorted(fn([rng.choice(P) for _ in P] + [rng.choice(B) for _ in B]) for _ in range(n))
    return [round(vals[int(0.025 * n)], 4), round(vals[int(0.975 * n) - 1], 4)]

def mcnemar(rows, a, b):
    """Exact two-sided McNemar on correct/incorrect (INVALID = incorrect)."""
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

frame = [json.loads(l) for l in open(f"{R}/out/frame.jsonl")] + [json.loads(l) for l in open(f"{R}/out/controls_frame.jsonl")]
frame = [r for r in frame if r["stratum"].split("|")[0] in ("M", "O", "CTRL")]
orig = {}
for p in (f"{R}/out/carbon_raw.jsonl", f"{R}/out/ctrl_raw.jsonl"):
    for l in open(p):
        x = json.loads(l); orig[x["id"]] = x  # last record wins, as in the first run
new = {}
for p in (RAW, CRAW):
    try:
        for l in open(p):
            x = json.loads(l); new[(x["arm"], x["id"])] = x
    except FileNotFoundError:
        pass
rows, shapes = [], collections.defaultdict(collections.Counter)
for r in frame:
    st = r["stratum"].split("|")[0]
    row = {k: r.get(k) for k in ("id", "label", "stratum", "gene_symbol", "mc_terms", "am_score", "oriented")}
    row["set"] = st
    row["C_orig"] = pred(orig.get(r["id"]), parse_17301) or "INVALID"
    row["missing"] = []
    for arm in ("F_plus", "F_gene", "C_reseed"):
        if arm == "C_reseed" and st != "M":
            continue
        key = (arm if not (arm == "F_gene" and r["oriented"] != "minus") else "F_plus", r["id"])
        x = new.get(key)
        if x is None or x.get("error"):  # infrastructure error = missing (retried), never scored as a model answer
            row["missing"].append(arm)
        row[arm] = pred(x, parse_vepqa if arm != "C_reseed" else parse_17301) or "INVALID"
        if row[arm] == "INVALID" and arm not in row["missing"]:
            shapes[f"{st}:{arm}"][invalid_shape(x)] += 1
        if x is not None:
            row[f"{arm}_sha"] = x["prompt_sha256"]
        if arm != "C_reseed":  # same answers re-parsed with the first run's parser: separates format from label changes
            row[f"{arm}_L"] = pred(x, parse_17301) or "INVALID"
    if r.get("am_score") is not None:
        row["A_bin"] = "pathogenic" if r["am_score"] > 0.5 else "benign"
    if r["mc_terms"] and len(r["mc_terms"]) == 1:
        row["R"] = "pathogenic" if r["mc_terms"][0] in RULE_P else "benign"
    rows.append(row)

def block(rs, arms):
    out = {"n": len(rs), "labels": dict(collections.Counter(r["label"] for r in rs))}
    for a in arms:
        b, rec = ba(rs, a)
        out[a] = {"BA": round(b, 4), "recall": {k: round(v, 4) for k, v in rec.items()},
                  "invalid": sum(r[a] == "INVALID" and a.removesuffix("_L") not in r.get("missing", []) for r in rs),
                  "missing": sum(a.removesuffix("_L") in r.get("missing", []) for r in rs),
                  "predicted": dict(sorted(collections.Counter(r[a] for r in rs).items()))}
    return out

tok = json.load(open(TOK))
res = {"tokcheck_pass": tok["pass"], "invalid_shapes": {k: dict(v) for k, v in sorted(shapes.items())}}
M = [r for r in rows if r["set"] == "M"]
O = [r for r in rows if r["set"] == "O"]
CT = [r for r in rows if r["set"] == "CTRL"]
res["missing"] = {s: {a: sum(a in r["missing"] for r in rows if r["set"] == s) for a in ("F_plus", "F_gene", "C_reseed")}
                  for s in ("M", "O", "CTRL")}
res["M"] = block(M, ["F_plus", "F_gene", "C_orig", "C_reseed", "A_bin", "F_plus_L", "F_gene_L"])
for a in ("F_plus", "F_gene", "C_reseed", "F_plus_L", "F_gene_L"):
    res["M"][a]["BA_CI95"] = boot(M, lambda s, a=a: ba(s, a)[0])
    res["M"][a]["D_Abin_minus_arm"] = round(res["M"]["A_bin"]["BA"] - res["M"][a]["BA"], 4)
    res["M"][a]["D_CI95"] = boot(M, lambda s, a=a: ba(s, "A_bin")[0] - ba(s, a)[0])
    res["M"][a]["delta_vs_C_orig"] = round(res["M"][a]["BA"] - res["M"]["C_orig"]["BA"], 4)
    res["M"][a]["delta_vs_C_orig_CI95"] = boot(M, lambda s, a=a: ba(s, a)[0] - ba(s, "C_orig")[0])
    res["M"][a]["mcnemar_vs_C_orig"] = mcnemar(M, a, "C_orig")
    res["M"][a]["label_flips_vs_C_orig"] = flips(M, a, "C_orig")
res["M"]["F_gene"]["mcnemar_vs_F_plus"] = mcnemar(M, "F_gene", "F_plus")
for o in ("plus", "minus"):
    res[f"M_genes_{o}_strand"] = block([r for r in M if r["oriented"] == o], ["F_plus", "F_gene", "C_orig", "A_bin"])
res["O"] = block(O, ["F_plus", "F_gene", "C_orig", "R"])
res["CTRL"] = block(CT, ["F_plus", "F_gene", "C_orig"])
gate = {a: {"invalid": res["CTRL"][a]["invalid"], "all_same_label": len({r[a] for r in CT}) == 1} for a in ("F_plus", "F_gene")}
for a in gate:
    gate[a]["pass"] = gate[a]["invalid"] <= 2 and not gate[a]["all_same_label"] and res["missing"]["CTRL"][a] == 0
res["CTRL_gate"] = gate

def reading(a):
    m = res["M"][a]
    if res["missing"]["M"][a]:
        return "INCOMPLETE"
    if not tok["pass"] or not gate[a]["pass"] or m["invalid"] > 30:
        return "INVALID"
    lo, hi = m["D_CI95"]
    if m["D_Abin_minus_arm"] >= 0.10 and lo > 0:
        return "GAP_HOLDS"
    if lo > 0:
        return "GAP_NARROWS"
    if hi < 0:
        return "GAP_FLIPS"
    return "GAP_CLOSES"

def prompt_effect(a):
    lo, hi = res["M"][a]["delta_vs_C_orig_CI95"]
    return "BA_HIGHER" if lo > 0 else "BA_LOWER" if hi < 0 else "NO_DETECTABLE_CHANGE"

res["reading_F_plus"] = reading("F_plus")
res["reading_F_gene"] = reading("F_gene")
# Headline: orientation is not stated by the publisher, so a reading stands only if both agree.
res["reading_headline"] = (res["reading_F_plus"] if res["reading_F_plus"] == res["reading_F_gene"] else
                           "INCOMPLETE" if "INCOMPLETE" in (res["reading_F_plus"], res["reading_F_gene"]) else
                           "INVALID" if "INVALID" in (res["reading_F_plus"], res["reading_F_gene"]) else
                           "ORIENTATION_DEPENDENT")
res["prompt_effect_F_plus"] = prompt_effect("F_plus")
res["prompt_effect_F_gene"] = prompt_effect("F_gene")
json.dump({"result": res, "rows": rows}, open(OUT, "w"), indent=1, sort_keys=True)
print(json.dumps(res, indent=1, sort_keys=True))
