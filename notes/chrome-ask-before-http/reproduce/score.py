"""Scorer (frozen before the run). Usage: python3 -I src/score.py out/a155.jsonl out/a157.jsonl > out/score.json"""
import json, math, os, sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
meta = json.loads((root / os.environ.get('META', 'out/sample-meta.json')).read_text(encoding='utf-8'))
def load(p):
    d = {}
    for l in open(p, encoding='utf-8'):
        if l.strip():
            r = json.loads(l); d[r['origin']] = r   # a later line (retry pass) replaces an earlier one
    return d
def cls(r):
    if r is None or r.get('error'): return 'RUN_ERROR'
    href, err = r.get('href') or '', r.get('navErrorText')
    if err == 'net::ERR_BLOCKED_BY_CLIENT': return 'BLOCKED'
    if href.startswith('https://'): return 'HTTPS'
    if href.startswith('http://'): return 'HTTP'
    if href.startswith('chrome-error://') and err is None: return 'ERRPAGE_NOERR'
    return 'NET_ERROR'
def wilson(k, n, z=1.96):
    if n == 0: return [None, None]
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round((c - h) / d, 4), round((c + h) / d, 4)]
a, b = load(sys.argv[1]), load(sys.argv[2])
origins = [o for o in (root / os.environ.get('SAMPLE', 'out/sample.txt')).read_text(encoding='utf-8').split() if o]
N = {'top': meta['top100k_http'], 'rest': meta['rest_http']}
res = {'pairs': {}, 'strata': {}}
for s in ('top', 'rest'):
    os_ = [o for o in origins if (meta['rank_bucket'][o] <= 100000) == (s == 'top')]
    cells = {}
    for o in os_:
        k = f'{cls(a.get(o))}->{cls(b.get(o))}'; cells[k] = cells.get(k, 0) + 1
        res['pairs'][o] = k
    n = len(os_); d = cells.get('HTTP->BLOCKED', 0) + sum(v for k, v in cells.items() if k.startswith('HTTP->') and k != 'HTTP->BLOCKED')
    warn = cells.get('HTTP->BLOCKED', 0)
    res['strata'][s] = {'n': n, 'frame_N': N[s], 'cells': dict(sorted(cells.items())), 'D_http_loaded_155': d, 'warn': warn,
                        'P_warn_given_http': round(warn / d, 4) if d else None, 'P_ci': wilson(warn, d),
                        'warn_share_of_sample': round(warn / n, 4), 'warn_share_ci': wilson(warn, n),
                        'est_frame_warn_origins': round(N[s] * warn / n)}
tot_est = sum(v['est_frame_warn_origins'] for v in res['strata'].values())
lo = sum(round(v['frame_N'] * v['warn_share_ci'][0]) for v in res['strata'].values())
hi = sum(round(v['frame_N'] * v['warn_share_ci'][1]) for v in res['strata'].values())
res['est_crux_top1m_warn_origins'] = {'point': tot_est, 'strat_sum_of_wilson_bounds': [lo, hi]}
dw = sum(v['D_http_loaded_155'] for v in res['strata'].values()); ww = sum(v['warn'] for v in res['strata'].values())
res['pooled_unweighted'] = {'D': dw, 'warn': ww, 'P': round(ww / dw, 4) if dw else None}
print(json.dumps(res, indent=1, sort_keys=True))
