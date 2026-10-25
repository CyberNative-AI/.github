"""Score verdicts against the decision rule fixed before judging (see the note).
  python3 -I src/score.py data/records.jsonl out/verdicts.jsonl [out/verdicts_t18.jsonl] > out/score.json
"""
import json
import random
import sys
from collections import Counter, defaultdict
from math import comb

PRIMARY = ["q38_27b_multi", "q38_27b_single128k", "fable5_single"]
SECONDARY = ["q38_fn_multi", "q38_fn_single"]
REPORTED = {"q38_27b_multi": 92.4, "q38_27b_single128k": 66.8, "fable5_single": 90.4,
            "q38_fn_multi": 93.0, "q38_fn_single": 84.2}
CAPMATCH_ARM = "q38_27b_single128k"


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def main(rec_path, ver_path, t18_path=None):
    recs = {r["key"]: r for r in load(rec_path)}
    ver = {v["key"]: v for v in load(ver_path)}
    t18 = {v["key"]: v for v in load(t18_path)} if t18_path else {}
    for k, v in ver.items():
        assert v["code_sha256"] == recs[k]["code_sha256"], k
    out = {"n_records": len(recs), "n_verdicts": len(ver), "arms": {}}
    per_q = defaultdict(lambda: defaultdict(list))  # arm -> qid -> [bool]
    for k, r in recs.items():
        if k in ver:
            per_q[r["arm"]][r["qid"]].append(ver[k]["verdict"] == "PASS")
    for arm in PRIMARY + SECONDARY:
        rows = [(recs[k], ver[k]) for k in recs if recs[k]["arm"] == arm and k in ver]
        if not rows:
            continue
        n = len(rows)
        ours = sum(v["verdict"] == "PASS" for _, v in rows)
        t18p = sum((t18.get(r["key"], v)["verdict"] == "PASS") for r, v in rows)
        matrix = Counter(f"stock={'P' if r['stock'] else 'F'} reported={'P' if r['reported'] else 'F'} ours={v['verdict']}"
                         for r, v in rows)
        g1_rows = [(r, v) for r, v in rows if r["stock"] and not (arm == CAPMATCH_ARM and not r["reported"])]
        g1 = sum(v["verdict"] == "PASS" for _, v in g1_rows) / max(1, len(g1_rows))
        corrected = [(r, v) for r, v in rows if r["reported"] and not r["stock"]]
        disagree = [{"key": r["key"], "reported": r["reported"], "stock": r["stock"], "ours": v["verdict"],
                     "fail_test": v.get("fail_test"), "max_t": v.get("max_t")}
                    for r, v in rows if r["reported"] != (v["verdict"] == "PASS")]
        q = per_q[arm]
        passk = [round(100 * sum(1 - comb(len(x) - sum(x), k) / comb(len(x), k) for x in q.values()) / len(q), 1)
                 for k in range(1, 6)] if all(len(x) == 5 for x in q.values()) and len(q) == 100 else None
        stdin = [qq for qq in q if not qq.isdigit()]
        func = [qq for qq in q if qq.isdigit()]
        m = lambda qs: round(100 * sum(sum(q[x]) / len(q[x]) for x in qs) / max(1, len(qs)), 1)
        out["arms"][arm] = {
            "n": n, "mean_ours": round(100 * ours / n, 2), "mean_reported": REPORTED[arm],
            "mean_reported_recomputed": round(100 * sum(r["reported"] for r, _ in rows) / n, 2),
            "mean_stock": round(100 * sum(r["stock"] for r, _ in rows) / n, 2),
            "mean_ours_t18_sensitivity": round(100 * t18p / n, 2),
            "G1_stock_pass_rate_ours": round(g1, 4), "G1_n": len(g1_rows),
            "corrected_to_pass": len(corrected),
            "corrected_to_pass_ours_pass": sum(v["verdict"] == "PASS" for _, v in corrected),
            "verdicts": dict(Counter(v["verdict"] for _, v in rows)),
            "lenient_rows": [r["key"] for r, v in rows if not r["stock"] and not r["reported"] and v["verdict"] == "PASS"],
            "g2_rows_to_read": [r["key"] for r, v in rows if r["reported"] and v["verdict"] in ("RE", "NOCODE", "JUDGE_ERR")],
            "matrix": dict(sorted(matrix.items())), "disagreements": disagree,
            "oracle_passk_1to5": passk, "stdin_mean": m(stdin), "functional_mean": m(func),
            "n_stdin": len(stdin), "n_functional": len(func),
        }
    A = out["arms"]
    if all(a in A for a in PRIMARY):
        qa, qb = per_q["q38_27b_multi"], per_q["fable5_single"]
        qs = sorted(set(qa) & set(qb))
        diff = [sum(qa[x]) / len(qa[x]) - sum(qb[x]) / len(qb[x]) for x in qs]
        d = 100 * sum(diff) / len(diff)
        rng = random.Random(16496)
        boots = sorted(100 * sum(rng.choice(diff) for _ in diff) / len(diff) for _ in range(10000))
        ci = [round(boots[249], 2), round(boots[9749], 2)]
        heads = ["q38_27b_multi", "fable5_single"]
        g1_rate = {a: A[a]["G1_stock_pass_rate_ours"] for a in PRIMARY}
        g1_gap = abs((1 - g1_rate["q38_27b_multi"]) - (1 - g1_rate["fable5_single"])) * 100
        g1 = all(r >= 0.99 for r in g1_rate.values()) and g1_gap <= 1.0
        c40 = A["q38_27b_multi"]["corrected_to_pass_ours_pass"]
        shifts = {a: round(A[a]["mean_ours"] - REPORTED[a], 2) for a in PRIMARY}
        shifts18 = {a: round(A[a]["mean_ours_t18_sensitivity"] - REPORTED[a], 2) for a in PRIMARY}
        lenient = {a: A[a]["lenient_rows"] for a in PRIMARY}
        if not g1:
            verdict = "INVALID (G1)"
        elif any(len(v) > 5 for v in lenient.values()):
            verdict = "HOLD (leniency check > 5)"
        elif ci[1] < 0 or c40 <= 30 or any(abs(shifts[a]) >= 2.0 and abs(shifts18[a]) >= 2.0 for a in heads):
            verdict = "CHANGED"
        elif c40 >= 36 and d >= 0 and ci[0] > -3.0 and all(abs(shifts[a]) <= 1.5 for a in heads):
            verdict = "CONFIRMED (pending G2 manual read)"
        else:
            verdict = "MIXED"
        out["decision"] = {"d_27Bmulti_minus_fable5": round(d, 2), "d_ci95": ci, "G1_all": g1,
                           "G1_rates": g1_rate, "G1_gap_pts": round(g1_gap, 2),
                           "corrected_40_ours_pass": c40, "shift_vs_reported": shifts,
                           "shift_vs_reported_t18": shifts18, "verdict": verdict}
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    print()


if __name__ == "__main__":
    main(*sys.argv[1:4])
