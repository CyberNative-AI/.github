"""Recompute every number in the note from counts.json (aggregate run-3 counts) and, if given, a variations seed file.
Usage: python3 -I check.py [seed.bin ...]     exit 0 = all PASS"""
import json, math, sys
from pathlib import Path
here = Path(__file__).resolve().parent
c = json.loads((here / 'counts.json').read_text(encoding='utf-8'))
fails = 0
def check(name, got, want):
    global fails
    ok = got == want; fails += not ok
    print(('PASS' if ok else 'FAIL'), name, got if ok else f'{got} != {want}')
def wilson(k, n, z=1.96):  # same formula as score.py
    p = k / n; d = 1 + z * z / n; ctr = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return round((ctr - h) / d, 4), round((ctr + h) / d, 4)
st = c['strata']
for s, (warn, d, pct) in {'top': (278, 300, 93), 'rest': (288, 322, 89)}.items():
    cells = st[s]['cells']
    D = sum(v for k, v in cells.items() if k.startswith('HTTP->'))
    check(f'{s}: stopped in 157 / opened over HTTP in 155', (cells['HTTP->BLOCKED'], D), (warn, d))
    check(f'{s}: percent', round(100 * warn / d), pct)
    check(f'{s}: sample size', sum(cells.values()), st[s]['n'])
check('frame http origins', st['top']['frame_N'] + st['rest']['frame_N'], c['frame']['http_origins'])
check('frame http origins = 7,748', c['frame']['http_origins'], 7748)
check('top stratum is a census', st['top']['n'], st['top']['frame_N'])
point = sum(round(v['frame_N'] * v['cells']['HTTP->BLOCKED'] / v['n']) for v in st.values())
lo = sum(round(v['frame_N'] * wilson(v['cells']['HTTP->BLOCKED'], v['n'])[0]) for v in st.values())
hi = sum(round(v['frame_N'] * wilson(v['cells']['HTTP->BLOCKED'], v['n'])[1]) for v in st.values())
check('estimate of top-1M origins stopped on first visit [bounds]', (point, lo, hi), (4452, 4113, 4782))
check('rounded for the note', (round(point, -1), round(lo, -1), round(hi, -1)), (4450, 4110, 4780))
nd = c['by_port']['nondefault_port']
check('non-default port: opened over HTTP in 155, then in 157', (sum(v for k, v in nd.items() if k.startswith('HTTP->')), nd.get('HTTP->HTTP', 0)), (33, 33))
dp = c['by_port']['default_port']
check('default port: stopped / opened over HTTP in 155', (dp['HTTP->BLOCKED'], sum(v for k, v in dp.items() if k.startswith('HTTP->'))), (566, 589))
check('rank buckets sum to strata', sum(v[0] for v in c['by_rank_bucket_stopped_of_http_in_155'].values()), 278 + 288)
n_all = st['top']['n'] + st['rest']['n']
unreach = sum(v for s in st.values() for k, v in s['cells'].items() if k.startswith('NET_ERROR->'))
check('no answer in 155 after retry', (unreach, n_all, round(100 * unreach / n_all, 1)), (196, 1002, 19.6))
for o in ('http://http.badssl.com', 'http://httpforever.com'):
    check(f'positive control {o}', c['controls_run3'][o], {'pre_a155': 'HTTP', 'post_a155': 'HTTP', 'pre_a157': 'BLOCKED', 'post_a157': 'BLOCKED'})
check('negative control http://example.com', set(c['controls_run3']['http://example.com'].values()), {'HTTPS'})
f = c['fix_arm']
check('HttpsOnlyMode=disallowed: retested, stopped, opened over HTTP', (f['retested_stopped_origins'], f['cells'].get('BLOCKED', 0), f['cells'].get('HTTP', 0)), (30, 0, 29))
for p in sys.argv[1:]:   # optional: seeds fetched by the reader (see seedparse.py)
    sys.path.insert(0, str(here)); import seedparse
    ss = list(seedparse.studies(p))
    check(f'{p}: one ask-before-HTTP study', len(ss), 1)
    for s in ss:
        tot = sum(w for _, w, _ in s['groups']); on = sum(w for _, w, f in s['groups'] if 'HttpsFirstBalancedModeAutoEnable' in f)
        check(f"{p}: {s['name']} share enabled {s['min']}..{s['max']} {s['channels']} {s['platforms']} other filters={s['other_filter_fields'] or 'none'}", (on, tot), (100, 100))
print('ALL PASS' if not fails else f'{fails} FAIL'); sys.exit(1 if fails else 0)
