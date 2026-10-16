"""Build all.tsv, sample100k.tsv, taut20k.tsv and dbstereo.tsv from chembl_37_chemreps.txt.gz in folder ARGV[1]."""
import gzip, random, sys
from pathlib import Path
d = Path(sys.argv[1])
rows = []
with gzip.open(d / "chembl_37_chemreps.txt.gz", "rt", encoding="utf-8", newline="") as f:
    next(f)
    for line in f:
        p = line.rstrip("\n").split("\t")
        rows.append((p[0], p[1]))
def w(name, rs):
    with open(d / name, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(f"{a}\t{b}\n" for a, b in rs)
w("all.tsv", rows)
idx = sorted(random.Random(14054).sample(range(len(rows)), 100000))
s = [rows[i] for i in idx]
w("sample100k.tsv", s)
w("taut20k.tsv", s[:20000])
w("dbstereo.tsv", [r for r in rows if "/" in r[1] or "\\" in r[1]])
print(len(rows))
