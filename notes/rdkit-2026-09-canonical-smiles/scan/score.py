"""Scorer. usage: python score.py OUT_ROOT RESULT_JSON
OUT_ROOT holds A-<arm>/, B-<arm>/, T-<arm>/, D/ chunk directories (arm in V1 V2 V3 V4 V4L).
"""
import json
import statistics
import sys
from pathlib import Path

ARMS = ["V1", "V2", "V3", "V4", "V4L"]


def load(d):
    out = {}
    for p in sorted(Path(d).glob("c*.jsonl")):
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            out[r["id"]] = r
    return out


def ok(r):
    return r is not None and "err" not in r


def churn(a, b, field):
    both = [k for k in a if ok(a[k]) and ok(b.get(k)) and field in a[k] and field in b[k]]
    ch = [k for k in both if a[k][field] != b[k][field]]
    return {"n": len(both), "changed": len(ch), "rate": len(ch) / len(both) if both else None}, ch


def health(run):
    ms = sorted(r.get("ms", 0) for r in run.values())
    errs = {}
    for r in run.values():
        if "err" in r:
            e = r["err"].split(":")[0]
            errs[e] = errs.get(e, 0) + 1
    return {"rows": len(run), "errors": errs, "ms_p50": ms[len(ms) // 2], "ms_p99": ms[int(len(ms) * .99)],
            "ms_max": ms[-1], "ms_sum_s": round(sum(ms) / 1000, 1)}


def contract(run, new=False):
    s = "_new" if new else ""
    rs = [r for r in run.values() if ok(r)]
    ik = "ikey_new" if new else "ikey"
    return {"n": len(rs),
            "not_idem": sum(1 for r in rs if (f"idem{s}" in r) and not r[f"idem{s}"]),
            "renumber_variant": sum(1 for r in rs if r.get("n_new" if new else "n_legacy", 1) > 1),
            "ikey_roundtrip_changed": sum(1 for r in rs if f"ikey_rt{s}" in r and r[f"ikey_rt{s}"] != r[ik])}


def main():
    root, dst = Path(sys.argv[1]), sys.argv[2]
    res = {"A": {}, "B": {}, "T": {}, "controls": {}, "examples": {}}
    A = {a: load(root / f"A-{a}") for a in ARMS}
    res["A"]["health"] = {a: health(A[a]) for a in ARMS}
    for x, y in [("V1", "V2"), ("V2", "V3"), ("V3", "V4"), ("V3", "V4L"), ("V4", "V4L")]:
        for f in ("iso", "flat", "nsymm", "nri"):
            res["A"][f"churn_{x}_{y}_{f}"], ch = churn(A[x], A[y], f)
            if f == "iso":
                res["examples"][f"{x}_{y}"] = [[k, A[x][k]["iso"], A[y][k]["iso"]] for k in ch[:40]]
    _, ch34 = churn(A["V3"], A["V4"], "iso")
    rest = [k for k in ch34 if ok(A["V4L"].get(k)) and A["V4L"][k]["iso"] == A["V3"][k]["iso"]]
    res["A"]["M2_restored"] = {"changed": len(ch34), "restored": len(rest),
                               "rate": len(rest) / len(ch34) if ch34 else None}
    res["A"]["not_idem_full"] = {a: contract(A[a])["not_idem"] for a in ARMS}
    res["examples"]["A_not_idem"] = {a: [[k, r["iso"]] for k, r in A[a].items() if ok(r) and not r["idem"]][:20]
                                     for a in ARMS}
    B = {a: load(root / f"B-{a}") for a in ARMS}
    res["B"]["health"] = {a: health(B[a]) for a in ARMS}
    res["B"]["contract_legacy"] = {a: contract(B[a]) for a in ARMS}
    res["B"]["contract_new"] = {a: contract(B[a], new=True) for a in ARMS}
    for f in ("fp", "ikey", "iso_new"):
        for x, y in [("V1", "V2"), ("V2", "V3"), ("V3", "V4"), ("V3", "V4L")]:
            res["B"][f"churn_{x}_{y}_{f}"], _ = churn(B[x], B[y], f)
    res["examples"]["B_not_idem_new"] = {a: [[k, r["iso_new"]] for k, r in B[a].items() if ok(r) and not r["idem_new"]][:20]
                                         for a in ARMS}
    res["examples"]["B_renumber_variant_legacy"] = {a: [k for k, r in B[a].items() if ok(r) and r["n_legacy"] > 1][:20]
                                                    for a in ARMS}
    T = {a: load(root / f"T-{a}") for a in ("V3", "V4", "V4L")}
    res["T"]["health"] = {a: health(T[a]) for a in T}
    for x, y in [("V3", "V4"), ("V3", "V4L")]:
        res["T"][f"churn_{x}_{y}_taut"], ch = churn(T[x], T[y], "taut")
        res["examples"][f"T_{x}_{y}"] = [[k, T[x][k]["taut"], T[y][k]["taut"]] for k in ch[:20]]
    D = load(root / "D")
    fields = sorted({f for r in B["V4"].values() for f in r} - {"ms", "id"})
    res["controls"]["C2_nondeterministic_fields"] = {
        f: sum(1 for k, r in B["V4"].items() if r.get(f) != D.get(k, {}).get(f)) for f in fields}
    res["controls"]["C1_ikey_churn"] = {k: v for k, v in res["B"].items() if k.endswith("_ikey")}
    # decisions
    m1 = res["A"]["churn_V3_V4_iso"]["rate"]
    comp = max(res["A"]["churn_V1_V2_iso"]["rate"], res["A"]["churn_V2_V3_iso"]["rate"])
    m2 = res["A"]["M2_restored"]["rate"]
    if m1 >= 0.001 and m1 >= 2 * comp:
        h1 = "H1_TRUE_RESTORED" if (m2 or 0) >= 0.9 else "H1_TRUE_UNRESTORED"
    elif m1 < 0.0001 and m1 <= comp:
        h1 = "STOP_DROP_IN"
    else:
        h1 = "BETWEEN"
    h2 = {}
    for scope, c3, c4 in [("B", res["B"]["contract_legacy"]["V3"], res["B"]["contract_legacy"]["V4"]),
                          ("A", {"not_idem": res["A"]["not_idem_full"]["V3"]}, {"not_idem": res["A"]["not_idem_full"]["V4"]})]:
        for k in c3:
            if k == "n":
                continue
            a, b = c3[k], c4[k]
            h2[f"{scope}_{k}"] = ("REGRESSION" if b >= 2 * a and b - a >= 10 else
                                  "FIX" if b <= 0.5 * a and a - b >= 10 else "NO_CHANGE")
    n_new = res["B"]["contract_new"]["V4"]
    r3 = n_new["not_idem"] / n_new["n"]
    h3 = "PREVALENT" if r3 >= 0.0005 else "RARE" if r3 < 0.00005 else "BETWEEN"
    res["decisions"] = {"H1": h1, "M1": m1, "comparator_max": comp, "M2": m2, "H2": h2, "H3": h3, "H3_rate": r3}
    Path(dst).write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(res["decisions"], indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
