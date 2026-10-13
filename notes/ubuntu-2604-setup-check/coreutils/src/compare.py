"""Compare arm outputs per case. Classes: same | stderr_only | material (rc zero/nonzero flip, stdout, or fs state).
usage: compare.py CASES A.jsonl B.jsonl [C.jsonl] -> prints JSON lines of differing cases."""
import json, re, sys


def load(p):
    return {r["id"]: r for r in map(json.loads, open(p))}


def norm_err(e):
    # program-name prefixes and quoting styles are not semantic
    return re.sub(r"[‘’'\"`]", "", e).strip().lower()


def klass(a, b):
    if a is None or b is None:
        return "missing"
    rc_a, rc_b = a["rc"], b["rc"]
    zero_a, zero_b = rc_a == 0, rc_b == 0
    diffs = []
    if zero_a != zero_b or (isinstance(rc_a, str) != isinstance(rc_b, str)):
        diffs.append("rc_flip")
    elif rc_a != rc_b:
        diffs.append("rc_value")
    if a["out_sha"] != b["out_sha"]:
        diffs.append("stdout")
    if a["fs_sha"] != b["fs_sha"]:
        diffs.append("fs")
    if norm_err(a["err"]) != norm_err(b["err"]):
        diffs.append("stderr")
    material = [d for d in diffs if d in ("rc_flip", "stdout", "fs")]
    if material:
        return "material:" + "+".join(material)
    if diffs:
        return "minor:" + "+".join(diffs)
    return "same"


def main(cases_p, *arms):
    cases = {r["id"]: r for r in map(json.loads, open(cases_p))}
    A = [load(p) for p in arms]
    for cid, c in sorted(cases.items()):
        a, b = A[0].get(cid), A[1].get(cid)
        k = klass(a, b)
        rec = {"id": cid, "argv": c["argv"], "mode": c["mode"], "control": c["control"], "piped_in": c["piped_in"], "class": k}
        if len(A) > 2:
            g = A[2].get(cid)
            rec["attr_vs_gnu94"] = klass(a, g)   # GNU 9.4 vs GNU 9.7
            rec["attr_vs_uutils"] = klass(g, b)  # GNU 9.7 vs uutils
        if k != "same":
            for nm, r in (("a", a), ("b", b)):
                if r: rec[nm] = {x: r.get(x) for x in ("rc", "out", "err", "fs_added", "fs_removed")}
        print(json.dumps(rec, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main(*sys.argv[1:])
