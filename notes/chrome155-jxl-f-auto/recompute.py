"""Recompute the note's numbers from images.csv, rendered.csv and quality.csv. Usage: python3 recompute.py"""
import csv, statistics
from collections import defaultdict
from pathlib import Path

here = Path(__file__).parent
rows = list(csv.DictReader((here / "images.csv").open(encoding="utf-8")))
ratio = lambda x: int(x["chrome155_bytes"]) / int(x["chrome154_bytes"])
rs = [ratio(x) for x in rows]
print(f"images where Chrome 155 got JPEG XL: {len(rows)}")
print(f"median bytes ratio (Chrome 155 / Chrome 154): {statistics.median(rs):.2f}")
bw = sum(int(x["chrome155_bytes"]) for x in rows) / sum(int(x["chrome154_bytes"]) for x in rows)
print(f"byte-weighted ratio: {bw:.2f}")
print(f"images at least 1.10x larger: {sum(r >= 1.10 for r in rs)}/{len(rs)}")
for fmt in sorted({x["chrome154_format"] for x in rows}):
    sub = [ratio(x) for x in rows if x["chrome154_format"] == fmt]
    print(f"  Chrome 154 got {fmt}: n={len(sub)}, median {statistics.median(sub):.2f}")
site = defaultdict(list)
for x in rows:
    site[x["site"]].append(ratio(x))
meds = {s: statistics.median(v) for s, v in site.items()}
print(f"sites: {len(meds)}; site median at least 1.10x: {sum(m >= 1.10 for m in meds.values())}")
print(f"delivery clusters: {len({x['cluster'] for x in rows})}")
asset = defaultdict(list)
for x in rows:
    asset[(x["site"], x["asset"])].append(ratio(x))
amed = {k: statistics.median(v) for k, v in asset.items()}
by_site = defaultdict(list)
for (s, _), m in amed.items():
    by_site[s].append(m)
print(f"per-site asset groups (heuristic URL grouping): {len(amed)}; median {statistics.median(amed.values()):.2f}; "
      f"sites whose median image is at least 1.10x: {sum(statistics.median(v) >= 1.10 for v in by_site.values())}")
ren = list(csv.DictReader((here / "rendered.csv").open(encoding="utf-8")))
rr = [ratio(x) for x in ren]
print(f"rendered pages: {len(ren)} images from {len({x['site'] for x in ren})} sites; median {statistics.median(rr):.2f}; "
      f"byte-weighted {sum(int(x['chrome155_bytes']) for x in ren) / sum(int(x['chrome154_bytes']) for x in ren):.2f}; "
      f"at least 1.10x: {sum(r >= 1.10 for r in rr)}; at most 0.90x: {sum(r <= 0.90 for r in rr)}")
for s in sorted({x["site"] for x in ren}):
    sub = [ratio(x) for x in ren if x["site"] == s]
    print(f"  {s}: rendered n={len(sub)} median {statistics.median(sub):.2f}; static-sample median {meds[s]:.2f}")
q = [x for x in csv.DictReader((here / "quality.csv").open(encoding="utf-8")) if not x["excluded"]]
uniq = {(x["ratio"], x["ssimulacra2_chrome154"], x["ssimulacra2_chrome155"]): x for x in q}.values()
d = [float(x["ssimulacra2_chrome155"]) - float(x["ssimulacra2_chrome154"]) for x in uniq]
print(f"quality: {len(q)} scored rows, {len(d)} distinct images; median SSIMULACRA2 gain {statistics.median(d):+.1f}; "
      f"lower score for Chrome 155: {sum(v < 0 for v in d)}")
