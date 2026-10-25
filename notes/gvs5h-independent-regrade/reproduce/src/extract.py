"""Build data/records.jsonl from a GVS5H clone (stored generations + the authors' verdicts).

usage: python3 -I src/extract.py <gvs5h-clone> <out-jsonl>

One row per (arm, pass, question): the stored code, its sha256, the verdict the authors
report (`reported`), and the stock-evaluator verdict before their corrections (`stock`).
Fable 5 and Flash-Next patched files carry no passed_before_regrade, so `stock` comes
from the unpatched file of the same pass.
"""
import glob
import hashlib
import json
import sys
from pathlib import Path

ARMS = {
    # arm: (reported-files glob, stock-files glob or None when the patched file carries it)
    "q38_27b_multi": ("runs/firstparty-128k-reasoning-on-5pass/results/q38_multiagent_p{p}.patched.json", None),
    "q38_27b_single128k": ("runs/firstparty-128k-reasoning-on-5pass/results/q38_single_p{p}.cap128k.patched.json", None),
    "fable5_single": ("runs/fable5-128k-reasoning-on-5pass/results/fable5_single_p{p}.patched.json",
                      "runs/fable5-128k-reasoning-on-5pass/results/fable5_single_p{p}.json"),
    "q38_fn_multi": ("runs/q38-fn-5pass/results/q38_fn_multiagent_p{p}.patched.json",
                     "runs/q38-fn-5pass/results/q38_fn_multiagent_p{p}.json"),
    "q38_fn_single": ("runs/q38-fn-5pass/results/q38_fn_single_p{p}.patched.json",
                      "runs/q38-fn-5pass/results/q38_fn_single_p{p}.json"),
}


def recs(path):
    return json.loads(Path(path).read_text())["lcb"]["records"]


def main(root, out):
    root = Path(root)
    rows = []
    for arm, (rep_pat, stock_pat) in ARMS.items():
        for p in range(1, 6):
            rep = recs(root / rep_pat.format(p=p))
            stock = {r["question_id"]: r for r in recs(root / stock_pat.format(p=p))} if stock_pat else None
            assert len(rep) == 100, (arm, p, len(rep))
            for r in rep:
                q = r["question_id"]
                if stock is not None:
                    s = stock[q]
                    assert s["code"] == r["code"], (arm, p, q, "stock/patched code differ")
                    stock_v = bool(s["passed"])
                else:
                    stock_v = bool(r["passed_before_regrade"])
                code = r["code"] or ""
                rows.append({
                    "key": f"{arm}|p{p}|{q}", "arm": arm, "pass": p, "qid": q, "code": code,
                    "code_sha256": hashlib.sha256(code.encode()).hexdigest(),
                    "reported": bool(r["passed"]), "stock": stock_v,
                    "status": r.get("status"), "finish_reason": r.get("finish_reason"),
                })
    rows.sort(key=lambda x: (x["qid"], x["arm"], x["pass"]))
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for x in rows:
            f.write(json.dumps(x, sort_keys=True) + "\n")
    print(len(rows), "rows ->", out)


if __name__ == "__main__":
    main(*sys.argv[1:3])
