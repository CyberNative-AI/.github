"""Compare a fresh-install rerun with the frozen rows and score.

usage: python rerun_compare.py FROZEN_RAW_DIR FROZEN_SCORE RERUN_DIR > diff-summary.json
Rows are matched by id. VAD text is compared as the parsed timestamp list. The pass rule, set before the
rerun: every row text identical, OR |dFTR_W| and |dFTR_W+V| <= 0.5 pp and the verdict is unchanged.
"""
import json
import sys
from pathlib import Path

ARMS = ("W_en", "VAD", "T_tiny")


def rows(p):
    return {r["id"]: r for r in map(json.loads, open(p, encoding="utf-8"))}


def main():
    raw, fscore, rer = Path(sys.argv[1]), json.load(open(sys.argv[2])), Path(sys.argv[3])
    rscore = json.load(open(rer / "score.json"))
    out = {"arms": {}}
    all_identical = True
    for arm in ARMS:
        f, r = rows(raw / f"{arm}.jsonl"), rows(rer / f"{arm}.jsonl")
        same = [i for i in f if i in r and f[i]["text"] == r[i]["text"] and f[i]["err"] == r[i]["err"]]
        diff = sorted(i for i in f if i in r and i not in set(same))
        by_set = {}
        for i in diff:
            by_set[f[i]["set"]] = by_set.get(f[i]["set"], 0) + 1
        out["arms"][arm] = {
            "frozen_n": len(f), "rerun_n": len(r), "ids_only_frozen": len(set(f) - set(r)),
            "ids_only_rerun": len(set(r) - set(f)), "identical": len(same), "differ": len(diff),
            "differ_by_set": by_set,
            "examples": [{"id": i, "frozen": f[i]["text"], "rerun": r[i]["text"]} for i in diff[:20]],
            "rerun_errors": sum(bool(x["err"]) for x in r.values()),
        }
        all_identical &= not diff and len(f) == len(r) == len(same)
    fp, rp = fscore["primary"], rscore["primary"]
    d_w = round(100 * (rp["ftr_W"] - fp["ftr_W"]), 3)
    d_wv = round(100 * (rp["ftr_WV"] - fp["ftr_WV"]), 3)
    rv, fv = rscore["verdict"].split(" ")[0], fscore["verdict"].split(" ")[0]
    out["primary"] = {"frozen": fp, "rerun": rp, "d_ftr_W_pp": d_w, "d_ftr_WV_pp": d_wv}
    out["gates"] = {"frozen": fscore["gates"], "rerun": rscore["gates"], "rerun_gates_ok": rscore.get("gates_ok")}
    out["verdict"] = {"frozen": fscore["verdict"], "rerun": rscore["verdict"]}
    out["all_rows_identical"] = all_identical
    out["within_tolerance"] = abs(d_w) <= 0.5 and abs(d_wv) <= 0.5 and rv == fv
    out["rerun_pass"] = all_identical or out["within_tolerance"]
    json.dump(out, sys.stdout, indent=1, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
