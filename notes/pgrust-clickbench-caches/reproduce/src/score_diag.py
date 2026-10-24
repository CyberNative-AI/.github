"""Diagnostic readout (dict_filter_cache off). usage: python3 -I score_diag.py out/diag > out/diag/summary.txt"""
import json, math, sys
from pathlib import Path
d = Path(sys.argv[1])
R = {}
for l in (d / 'X.jsonl').read_text(encoding='utf-8').splitlines():
    x = json.loads(l)
    if x['event'] == 'run':
        R.setdefault((x['mode'], x['q']), {})[x['run']] = x
modes = ['full+nodict', 'rows+nodict', 'granule', 'full']
shown = {m: sorted({r['mode_shown'] for (mm, q), rr in R.items() if mm == m for r in rr.values()}) for m in modes}
hot = {k: min(v[2]['ms'], v[3]['ms']) / 1000 for k, v in R.items()}
errs = sorted({k for k, v in R.items() for r in v.values() if r['err'] or r['rc']})
gm = lambda xs: math.exp(sum(map(math.log, xs)) / len(xs))
print('mode_shown', shown, 'errors', errs)
for m in modes:
    allq = gm([hot[(m, q)] + 0.01 for q in range(43)]) / gm([hot[('granule', q)] + 0.01 for q in range(43)])
    ex = [q for q in range(43) if q not in (20, 21, 22)]
    exq = gm([hot[(m, q)] + 0.01 for q in ex]) / gm([hot[('granule', q)] + 0.01 for q in ex])
    print(f'{m:12s} /granule all {allq:.3f}  without q20-22 {exq:.3f}')
print('q  ' + '  '.join(modes) + '  (hot ms)')
for q in (1, 20, 21, 22, 23, 28, 31):
    print(q, '  '.join(f'{hot[(m, q)] * 1000:.2f}' for m in modes))
