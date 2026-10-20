"""Frame + sample: CrUX 202609 global top-1M http:// origins (zakird/crux-top-lists).
All origins in rank buckets <=100k, plus a seeded uniform sample of 500 from the 500k and 1M buckets."""
import csv, gzip, json, random, sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
rows = list(csv.reader(gzip.open(root / 'raw/crux-202609.csv.gz', 'rt', encoding='utf-8')))[1:]
http = [(o, int(r)) for o, r in rows if o.startswith('http://')]
top = sorted(o for o, r in http if r <= 100000)
rest = sorted(o for o, r in http if r > 100000)
rng = random.Random(15015)
samp = sorted(rng.sample(rest, 500))
strata = {o: r for o, r in http}
(root / 'out').mkdir(exist_ok=True)
(root / 'out/sample.txt').write_text('\n'.join(top + samp) + '\n', encoding='utf-8')
meta = {'frame_total_origins': len(rows), 'frame_http': len(http), 'top100k_http': len(top), 'rest_http': len(rest),
        'sample_top': len(top), 'sample_rest': len(samp), 'seed': 15015,
        'rank_bucket': {o: strata[o] for o in top + samp}}
(root / 'out/sample-meta.json').write_text(json.dumps(meta, indent=1, sort_keys=True) + '\n', encoding='utf-8')
print({k: v for k, v in meta.items() if k != 'rank_bucket'})
