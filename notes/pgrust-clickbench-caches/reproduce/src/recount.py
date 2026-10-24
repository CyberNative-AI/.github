"""Second, independent recount of the headline numbers from the raw JSONL and EXPLAIN files (not score.py).
usage: python3 -I recount.py OUTDIR"""
import json, math, re, sys
from pathlib import Path
from collections import defaultdict
OUT = Path(sys.argv[1])

def load(p):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]

def hot(rows):
    t = defaultdict(dict)
    for r in rows:
        if r.get("event") == "run":
            t[(r["mode"], r["q"])][r["run"]] = (r["ms"], r["rc"], r["err"], r.get("res_sha"))
    return t

def gm(vals):
    return math.exp(sum(math.log(v) for v in vals) / len(vals))

def readout(path):
    if not path.exists():
        return None
    tot = None
    for m in re.finditer(r"Granules:\s*(\d+)\s*read", path.read_text()):
        tot = (tot or 0) + int(m.group(1))
    return tot

for rep in ("rep-a", "rep-b", "diag"):
    d = OUT / rep
    T = hot(load(d / "T.jsonl")) if (d / "T.jsonl").exists() else None
    if T is None:
        # diag file layout
        cands = list(d.glob("*.jsonl"))
        print(rep, "jsonl files:", [c.name for c in cands])
        T = hot([r for c in cands for r in load(c)])
    modes = sorted({m for m, _ in T})
    qs = sorted({q for _, q in T})
    errs = [(m, q, r) for (m, q), runs in T.items() for r, v in runs.items() if v[1] != 0 or v[2] != 0]
    H = {(m, q): min(T[(m, q)][2][0], T[(m, q)][3][0]) for (m, q) in T}
    C = {(m, q): T[(m, q)][1][0] for (m, q) in T}
    print(f"== {rep}: modes {modes}, {len(qs)} queries, errors {len(errs)}")
    g = {m: gm([H[(m, q)] / 1000 + 0.01 for q in qs]) for m in modes}
    gc = {m: gm([C[(m, q)] / 1000 + 0.01 for q in qs]) for m in modes}
    base = "granule"
    for m in modes:
        print(f"  hot {m:12s}/granule {g[m]/g[base]:.3f}   cold {gc[m]/gc[base]:.3f}" + (f"   /off {g[m]/g['off']:.3f}" if 'off' in g else ""))
    if "full" in modes:
        # only q20-22 at full, rest granule
        mix = gm([(H[("full", q)] if q in (20, 21, 22) else H[(base, q)]) / 1000 + 0.01 for q in qs])
        print(f"  q20-22 swapped in alone: {mix/g[base]:.3f}")
        rest = [q for q in qs if q not in (20, 21, 22)]
        for m in modes:
            print(f"  without q20-22 {m}/granule {gm([H[(m,q)]/1000+0.01 for q in rest])/gm([H[(base,q)]/1000+0.01 for q in rest]):.3f}")
        for q in (1, 20, 21, 22):
            print("  q%d hot ms " % q + " ".join(f"{m}={H[(m,q)]:.2f}" for m in modes) + f"  full/granule={H[('full',q)]/H[(base,q)]:.2f}")
    # readouts
    for q in (1, 20):
        tag = "x" if rep == "diag" else "t"
        ro = {m: readout(d / f"explain-{tag}-s16-{m}-q{q}.txt") for m in modes}
        print(f"  q{q} granules read (warm EXPLAIN):", ro)
    # REUSE: full read==0, granule read>0
    reuse = []
    for q in qs:
        tag = "x" if rep == "diag" else "t"
        f = readout(d / f"explain-{tag}-s16-full-q{q}.txt") if "full" in modes else None
        gr = readout(d / f"explain-{tag}-s16-granule-q{q}.txt")
        if f == 0 and gr and gr > 0:
            reuse.append(q)
    print("  REUSE (T-arm explain):", reuse)
    if (d / "D.jsonl").exists():
        D = hot(load(d / "D.jsonl"))
        wrong = [(m, q) for (m, q), runs in D.items() if m != "off" and runs[2][3] != D[("off", q)][2][3]]
        print("  D wrong vs off:", wrong)
        tdiff = sorted({q for (m, q), runs in T.items() if m != "off" and runs[2][3] != T[("off", q)][2][3]})
        print("  T res_sha differs from off (run 2):", tdiff)
    if (d / "S.jsonl").exists():
        S = [r for r in load(d / "S.jsonl") if r.get("event") == "stale"]
        valid = [r for r in S if (r["cold_q1"], r["cold_q20"]) != (r["before_q1"], r["before_q20"])]
        stale = [r for r in valid if (r["warm_q1"], r["warm_q20"]) != (r["cold_q1"], r["cold_q20"])]
        print(f"  S rows {len(S)}, valid {len(valid)}, stale {len(stale)}")
