"""Post-hoc (exploratory) numbers quoted in the note -> out/posthoc.json. Read-only over cached calls."""
import json, sys
from collections import Counter
sys.path.insert(0, 'src')
from collect import frame, search, T1, decided90
reg, M, iv, indep, eligible, rows = frame()
ivl = {k.lower(): v for k, v in reg['intervals'].items()}
out = {}
for cut in ('cut1', 'cut2'):
    info = json.load(open(f'out/{cut}_dropped_count_repos.json')); w = info['windows']
    relisted = [x for x in info['repos'] if any(w['post'][0] <= a <= w['post'][1] for a, b in ivl[x])]
    rs = [x for x in info['repos'] if x not in relisted]; S = set(rs)
    nm = {k: sum(1 for r in rows if r['repo'].lower() in S and w[k][0] <= r['created_at'] <= w[k][1]) for k in w}
    tot = {k: sum(search(f'repo:{x} type:pr created:{w[k][0]}..{w[k][1]}')[1] for x in rs) for k in w}
    nc = {k: tot[k] - nm[k] for k in w}
    post_top = Counter(r['repo'] for r in rows if r['repo'].lower() in set(info['repos']) and w['post'][0] <= r['created_at'] <= w['post'][1]).most_common(3)
    out[cut] = {'relisted_in_post': relisted, 'repos_excl': len(rs), 'N_m': nm, 'N_c': nc,
                'ratio_excl_relisted': (nm['post'] / nm['pre']) / (nc['post'] / nc['pre']) if nm['pre'] else None,
                'placebo_excl_relisted': (nm['pre'] / nm['prepre']) / (nc['pre'] / nc['prepre']) if nm['prepre'] else None,
                'post_top_repos_all': post_top}
INS = {'OWNER', 'MEMBER', 'COLLABORATOR'}
units = [r for r in rows if indep(r['repo']) and eligible(r['repo'], r['created_at']) and r['created_at'] < T1
         and not r.get('draft') and r['assoc'] not in INS and decided90(r)]
out['h1_top_repos_decided'] = Counter(r['repo'] for r in units).most_common(5)
e4 = json.load(open('out/e4_control.json'))
out['e4'] = {'control_probed': len(e4), 'control_422': sum(v == 422 for v in e4.values()),
             'miners_api': 182, 'miners_unsearchable': len(json.load(open('raw/unsearchable_accounts.json')))}
json.dump(out, open('out/posthoc.json', 'w'), indent=1, default=str)
print(json.dumps({k: (v.get('ratio_excl_relisted'), v.get('N_m')) if isinstance(v, dict) and 'N_m' in v else v for k, v in out.items()}, default=str))
