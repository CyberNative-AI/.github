"""Compute: frozen outcome rules, rates, Wilson/Newcombe CIs, Fisher p, merger gates, ruling.

Usage: python3 -I src/compute.py OUTDIR  -> OUTDIR/out/results.json (+ printed summary)
"""
import collections
import datetime as dt
import json
import math
import pathlib
import re
import sys

SMALL_LINES, SMALL_FILES = 30, 2
SLACK_S = 300


def t(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def outcome(r, h, read_time):
    c0 = t(r["created_at"])
    lim = c0 + dt.timedelta(hours=h)
    if lim > read_time:
        return None
    closed = t(r["closed_at"])
    closed_in = closed is not None and closed <= lim
    if r["is_pr"]:
        m = t(r.get("merged_at"))
        if m and m <= lim:
            return "ACCEPTED"
        if closed_in:
            if r.get("closed_commit_ids"):
                return "ACCEPTED"
            for x in r.get("xref_prs", []):
                xm = t(x["merged_at"])
                if xm and xm <= lim and x["number"] != r["number"]:
                    return "ACCEPTED"
            return "CLOSED_UNACCEPTED"
        return "OPEN"
    if not closed_in:
        return "OPEN"
    if r.get("state_reason") in ("not_planned", "duplicate"):
        return "NOT_PLANNED"
    if r.get("closed_commit_ids"):
        return "ACCEPTED"
    for x in r.get("xref_prs", []):
        xm = t(x["merged_at"])
        if xm and xm <= lim and xm <= closed + dt.timedelta(seconds=SLACK_S):
            return "ACCEPTED"
    return "COMPLETED_NOFIX"


def raw_outcome(r, h, read_time):
    c0 = t(r["created_at"])
    lim = c0 + dt.timedelta(hours=h)
    if lim > read_time:
        return None
    if r["is_pr"]:
        m = t(r.get("merged_at"))
        return "MERGED" if m and m <= lim else "NOT"
    cl = t(r["closed_at"])
    return "COMPLETED" if cl and cl <= lim and r.get("state_reason") == "completed" else "NOT"


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    w = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - w), min(1.0, c + w))


def newcombe(k1, n1, k2, n2):
    p1, l1, u1 = wilson(k1, n1)
    p2, l2, u2 = wilson(k2, n2)
    if p1 is None or p2 is None:
        return (None, None, None)
    d = p1 - p2
    return (d, d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2))


def fisher(k1, n1, k2, n2):
    K, N = k1 + k2, n1 + n2

    def pmf(a):
        return math.comb(n1, a) * math.comb(n2, K - a) / math.comb(N, K)
    lo, hi = max(0, K - n2), min(K, n1)
    p0 = pmf(k1)
    return min(1.0, sum(pmf(a) for a in range(lo, hi + 1) if pmf(a) <= p0 * (1 + 1e-9)))


def small(r):
    return (not r.get("draft")) and r.get("additions") is not None and \
        r["additions"] + r["deletions"] <= SMALL_LINES and r["changed_files"] <= SMALL_FILES


def main():
    out = pathlib.Path(sys.argv[1])
    meta = json.loads((out / "data" / "fetch-meta.json").read_text())
    read_time = t(meta["read_time"])
    rows = [json.loads(l) for l in open(out / "data" / "items.jsonl", encoding="utf-8")]
    res = {"read_time": meta["read_time"], "groups": {}, "tests": {}}
    sets = {
        "F_pr": [r for r in rows if r["group"] == "F" and r["is_pr"]],
        "F_small_pr": [r for r in rows if r["group"] == "F" and r["is_pr"] and small(r)],
        "O_prior_pr": [r for r in rows if r["group"] == "O_prior" and r["is_pr"]],
        "O_small_prior_pr": [r for r in rows if r["group"] == "O_prior" and r["is_pr"] and small(r)],
        "O_fix_prior_pr": [r for r in rows if r["group"] == "O_prior" and r["is_pr"] and re.search(r"(?i)\bfix", r["title"])],
        "O_same_pr": [r for r in rows if r["group"] == "O_same" and r["is_pr"]],
        "O_small_same_pr": [r for r in rows if r["group"] == "O_same" and r["is_pr"] and small(r)],
        "I_prior_pr": [r for r in rows if r["group"] == "I_prior" and r["is_pr"]],
        "F_issue": [r for r in rows if r["group"] == "F" and not r["is_pr"]],
        "O_prior_issue": [r for r in rows if r["group"] == "O_prior" and not r["is_pr"]],
        "O_same_issue": [r for r in rows if r["group"] == "O_same" and not r["is_pr"]],
        "I_prior_issue": [r for r in rows if r["group"] == "I_prior" and not r["is_pr"]],
    }
    for name, rs in sets.items():
        g = {"n_total": len(rs)}
        for h in (24, 72):
            oc = collections.Counter(outcome(r, h, read_time) for r in rs)
            oc.pop(None, None)
            n = sum(oc.values())
            k = oc.get("ACCEPTED", 0)
            rc = collections.Counter(raw_outcome(r, h, read_time) for r in rs)
            rc.pop(None, None)
            g[f"h{h}"] = {"n": n, "outcomes": dict(sorted(oc.items())), "accepted_rate_wilson": wilson(k, n),
                          "raw": dict(sorted(rc.items()))}
        res["groups"][name] = g

    def acc(name, h):
        rs = [r for r in sets[name] if outcome(r, h, read_time) is not None]
        return sum(outcome(r, h, read_time) == "ACCEPTED" for r in rs), len(rs)

    for a, b, h in (("F_small_pr", "O_small_prior_pr", 24), ("F_pr", "O_prior_pr", 24), ("F_pr", "O_fix_prior_pr", 24),
                    ("F_small_pr", "O_small_same_pr", 24), ("F_small_pr", "O_small_prior_pr", 72),
                    ("F_issue", "O_prior_issue", 72), ("F_issue", "O_prior_issue", 24), ("F_issue", "O_same_issue", 24)):
        k1, n1 = acc(a, h)
        k2, n2 = acc(b, h)
        res["tests"][f"{a}_vs_{b}_h{h}"] = {"k1": k1, "n1": n1, "k2": k2, "n2": n2,
                                            "diff_newcombe": newcombe(k1, n1, k2, n2), "fisher_p": fisher(k1, n1, k2, n2) if n1 and n2 else None}

    # Gates on the primary test.
    fs = [r for r in sets["F_small_pr"] if outcome(r, 24, read_time) == "ACCEPTED"]
    mergers = collections.Counter(r.get("merged_by") or "(closed-accepted)" for r in fs)
    clusters = collections.Counter(f"{r.get('merged_by')}|{(r.get('merged_at') or '')[:10]}" for r in fs)
    k1, n1 = acc("F_small_pr", 24)
    k2, n2 = acc("O_small_prior_pr", 24)
    top, topk = (mergers.most_common(1)[0] if mergers else (None, 0))
    loo = (k1 - topk) / n1 if n1 else None
    o_pt = k2 / n2 if n2 else None
    distinct = len([m for m in mergers if m != "(closed-accepted)"])
    lb = res["tests"]["F_small_pr_vs_O_small_prior_pr_h24"]["diff_newcombe"][1]
    gate_a = distinct >= 3
    gate_b = loo is not None and o_pt is not None and loo > o_pt
    if lb is None:
        ruling = "INCOMPLETE"
    elif lb > 0 and gate_a and gate_b:
        ruling = "ACCEPTED_FASTER"
    elif lb > 0:
        ruling = "BATCH_MERGED_NOT_GENERAL"
    else:
        ruling = "NO_ADVANTAGE"
    res["gates"] = {"mergers": dict(mergers.most_common()), "clusters": dict(clusters.most_common()),
                    "distinct_mergers": distinct, "gate_a_ge3_mergers": gate_a, "top_merger": top,
                    "leave_top_out_rate": loo, "o_small_prior_point": o_pt, "gate_b_loo_gt_o": gate_b}
    res["ruling"] = ruling
    (out / "out").mkdir(exist_ok=True)
    (out / "out" / "results.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"ruling": ruling, "gates": res["gates"], "tests": res["tests"]}, indent=1))


if __name__ == "__main__":
    main()
