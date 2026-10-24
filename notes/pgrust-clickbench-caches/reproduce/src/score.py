"""Score the two replicates (rules in ../README.md, 'How we measured'). usage: python3 -I score.py OUTDIR  (reads OUTDIR/rep-*/, writes OUTDIR/score.json)"""
import json, math, re, sys
from pathlib import Path

MODES = ['full', 'rows', 'granule', 'off']
NP = 16  # partitions; set by --npart for the pipeline dry run only
GRAN = re.compile(r'Granules:\s+(\d+) read,\s+(\d+) skipped,\s+(\d+) answered')


def load(p):
    return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]


def runs(rows):
    R = {}
    for d in rows:
        if d['event'] == 'run':
            R.setdefault((d['mode'], d['q']), {})[d['run']] = d
    return R


def readout(path):
    if not path.exists():
        return None
    hits = GRAN.findall(path.read_text(encoding='utf-8', errors='replace'))
    if not hits:
        return None
    return {'read': sum(int(h[0]) for h in hits), 'skipped': sum(int(h[1]) for h in hits),
            'answered': sum(int(h[2]) for h in hits)}


def gm(xs):
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def score_rep(rd):
    T = runs(load(rd / 'T.jsonl'))
    D = runs(load(rd / 'D.jsonl'))
    loads = [d for d in load(rd / 'T.jsonl') if d['event'] == 'load']
    nq = 1 + max(q for (_, q) in T)
    errq = sorted({q for (m, q), rr in T.items() for r in rr.values() if r['err'] or r['rc'] or r['ms'] is None})
    ok = [q for q in range(nq) if q not in errq]
    hot = {(m, q): min(T[(m, q)][2]['ms'], T[(m, q)][3]['ms']) / 1000 for m in MODES for q in ok}
    cold = {(m, q): T[(m, q)][1]['ms'] / 1000 for m in MODES for q in ok}
    g = {m: gm([hot[(m, q)] + 0.01 for q in ok]) for m in MODES}
    gc = {m: gm([cold[(m, q)] + 0.01 for q in ok]) for m in MODES}
    ro = {(m, q): readout(rd / f'explain-t-s{NP}-{m}-q{q}.txt') for m in MODES for q in range(nq)}
    reuse = [q for q in range(nq) if ro[('full', q)] and ro[('granule', q)]
             and ro[('full', q)]['read'] == 0 and ro[('granule', q)]['read'] > 0]
    reuse_rows = [q for q in range(nq) if ro[('rows', q)] and ro[('granule', q)]
                  and ro[('rows', q)]['read'] == 0 and ro[('granule', q)]['read'] > 0]
    t_diff = {m: [q for q in range(nq) if (m, q) in T and ('off', q) in T and
                  {T[(m, q)][r]['res_sha'] for r in (2, 3)} != {T[('off', q)][r]['res_sha'] for r in (2, 3)}]
              for m in MODES[:3]}
    d_err = sorted({q for (m, q), rr in D.items() for r in rr.values() if r['err'] or r['rc']})
    wrong = {m: [q for q in range(nq) if (m, q) in D and ('off', q) in D and q not in d_err and
                 D[(m, q)][2]['res_sha'] != D[('off', q)][2]['res_sha']] for m in MODES[:3]}
    S = [d for d in load(rd / 'S.jsonl') if d['event'] == 'stale']
    stale = []
    for s in S:
        for qn in ('q1', 'q20'):
            valid = s[f'cold_{qn}'] != s[f'before_{qn}']
            stale.append({'mode': s['mode'], 'mut': s['mut'], 'query': qn, 'valid': valid,
                          'before': s[f'before_{qn}'], 'warm': s[f'warm_{qn}'], 'cold': s[f'cold_{qn}'],
                          'stale': valid and s[f'warm_{qn}'] != s[f'cold_{qn}']})
    per_q = []
    for q in ok:
        per_q.append({'q': q, **{f'hot_ms_{m}': round(hot[(m, q)] * 1000, 3) for m in MODES},
                      **{f'read_{m}': (ro[(m, q)] or {}).get('read') for m in MODES},
                      'full_over_granule': round((hot[('full', q)] + 0.01) / (hot[('granule', q)] + 0.01), 4)})
    return {'load': loads, 'n_queries': nq, 'error_queries': errq,
            'geomean_hot_plus10ms': g, 'geomean_cold_plus10ms': gc,
            'ratio_full_granule': g['full'] / g['granule'], 'ratio_full_off': g['full'] / g['off'],
            'ratio_rows_granule': g['rows'] / g['granule'], 'ratio_granule_off': g['granule'] / g['off'],
            'cold_ratio_full_granule': gc['full'] / gc['granule'],
            'reuse_full': reuse, 'reuse_rows': reuse_rows,
            'no_readout': {m: [q for q in range(nq) if ro[(m, q)] is None] for m in MODES},
            't_answer_diff_vs_off': t_diff, 'd_error_queries': d_err, 'wrong_answers_vs_off': wrong,
            'stale': stale, 'per_query': per_q}


def main():
    global NP
    if '--npart' in sys.argv:
        NP = int(sys.argv[sys.argv.index('--npart') + 1])
    out = Path(sys.argv[1])
    reps = {p.name: score_rep(p) for p in sorted(out.glob('rep-*')) if (p / 'DONE').exists()}
    names = sorted(reps)
    v = {}
    if len(names) == 2:
        a, b = (reps[n] for n in names)
        reuse = sorted(set(a['reuse_full']) & set(b['reuse_full']))
        r = [a['ratio_full_granule'], b['ratio_full_granule']]
        rows_a = [x['rows'] for x in a['load']]; rows_b = [x['rows'] for x in b['load']]
        off_err = len(a['error_queries'])
        invalid = rows_a != rows_b or off_err > 2
        if invalid:
            score_v = 'INVALID'
        elif reuse and all(x <= 0.95 for x in r):
            score_v = 'CHANGE'
        elif all(0.95 <= x <= 1.05 for x in r):
            score_v = 'NEGATIVE'
        else:
            score_v = 'INCONCLUSIVE'
        wrong = any(qs for rep in (a, b) for qs in rep['wrong_answers_vs_off'].values())
        stale = any(s['stale'] for rep in (a, b) for s in rep['stale'])
        v = {'score_verdict': score_v, 'reuse_both_reps': reuse, 'ratio_full_granule': r,
             'ratio_full_off': [a['ratio_full_off'], b['ratio_full_off']],
             'correctness_verdict': 'CHANGE' if (wrong or stale) else 'NO_DEFECT_FOUND',
             'invalid_stale_rows': sum(1 for rep in (a, b) for s in rep['stale'] if not s['valid'])}
    res = {'verdict': v, 'reps': reps}
    (out / 'score.json').write_text(json.dumps(res, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(v, indent=1))
    for n in names:
        x = reps[n]
        print(n, 'rows', [l['rows'] for l in x['load']], 'errors', x['error_queries'],
              'full/gran %.3f full/off %.3f rows/gran %.3f gran/off %.3f cold full/gran %.3f' % (
                  x['ratio_full_granule'], x['ratio_full_off'], x['ratio_rows_granule'], x['ratio_granule_off'],
                  x['cold_ratio_full_granule']),
              'reuse', x['reuse_full'], 'wrong', x['wrong_answers_vs_off'],
              'stale', [s for s in x['stale'] if s['stale']], 'invalid S', sum(not s['valid'] for s in x['stale']))


if __name__ == '__main__':
    main()
