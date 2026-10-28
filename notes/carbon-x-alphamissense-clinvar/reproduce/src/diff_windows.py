"""New definitive ClinVar SNV labels between T0 and T1, with the first release window in which each became definitive.
usage: diff_windows.py T0.vcf.gz MID1.vcf.gz ... T1.vcf.gz out.jsonl   (releases in date order)"""
import json, sys, collections
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from diff_clinvar_lib import load, PATH, BEN, STAR
paths, out = sys.argv[1:-1], sys.argv[-1]
names = [p.rsplit("clinvar_", 1)[1][:8] for p in paths]
sig = [load(p, True) for p in paths[:-1]]
t1 = load(paths[-1], False)
rows, cnt = [], collections.Counter()
for vid, r in t1.items():
    if r["vc"] != "single_nucleotide_variant" or len(r["ref"]) != 1 or len(r["alt"]) != 1:
        continue
    lab = "pathogenic" if r["clnsig"] in PATH else "benign" if r["clnsig"] in BEN else None
    if lab is None or r["revstat"] not in STAR:
        continue
    if sig[0].get(vid) in PATH | BEN:
        continue
    first = next((names[i] for i in range(1, len(sig)) if sig[i].get(vid) in PATH | BEN), names[-1])
    terms = sorted({x.split("|")[1] for x in r["mc"].split(",") if "|" in x})
    r.update(label=lab, prev=sig[0].get(vid), first_window_end=first, mc_terms=terms)
    rows.append(r)
    cnt[(first, lab)] += 1
rows.sort(key=lambda r: int(r["id"]))
with open(out, "w") as f:
    for r in rows:
        f.write(json.dumps(r, sort_keys=True) + "\n")
print(json.dumps({"releases": names, "n": len(rows), "by_window_label": {f"{a}|{b}": n for (a, b), n in sorted(cnt.items())}}, indent=1))
c2 = collections.Counter((";".join(r["mc_terms"]) or "NONE", r["label"]) for r in rows)
for k, n in c2.most_common(16):
    print(n, k)
