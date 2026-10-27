"""Second run: share of search-hidden logins among 182 outside authors of PRs to the April 9 (cut 1) repositories
in the 32 days before that removal (seed 16784).

python3 src/april_control.py               draw the sample, probe each login, write raw/april_control_logins.json + out/april_control.json
python3 src/april_control.py --draw-only   print the drawn sample (offline)
python3 src/april_control.py --from-logins check an existing raw/april_control_logins.json against the draw, rewrite out/april_control.json (offline)

Needs raw/removal/cut1_pre.jsonl (README step 7), raw/api_miners.json and raw/tag_prs.jsonl.
Eligible: logins in the cut-1 pre-window pull that are not bots, not registered miners, not Gittensor-tagline authors
(collector or pulled window), with author association NONE, FIRST_TIMER, FIRST_TIME_CONTRIBUTOR or CONTRIBUTOR.
Draw: sort the eligible logins, shuffle with random.Random(16784), keep the first 182. The second run did not record
this rule; we recovered it afterwards, and it rebuilds that run's sample exactly (same 182 logins, same order).
Probe: author: search per login; for each HTTP 422, /users/{login} says whether the account still exists.
out/april_control.json replaces each login with its position in the sorted sample (a001..a182).
"""
import json, os, random, sys, time, urllib.parse
sys.path.insert(0, 'src'); import gh
OK_ASSOC = ('NONE', 'FIRST_TIMER', 'FIRST_TIME_CONTRIBUTOR', 'CONTRIBUTOR')
rows = [r for r in map(json.loads, open('raw/removal/cut1_pre.jsonl')) if '_q' not in r]
M = {m['githubUsername'].lower() for m in json.load(open('raw/api_miners.json')) if m.get('githubUsername')}
M |= {json.loads(l)['author'].lower() for l in open('raw/tag_prs.jsonl') if json.loads(l).get('author')}
M |= {r['login'].lower() for r in rows if r['tag'] and r['login']}
pool = sorted({r['login'] for r in rows if r['login'] and not r['login'].endswith('[bot]') and r['type'] != 'Bot'
               and r['assoc'] in OK_ASSOC and r['login'].lower() not in M})
p = list(pool); random.Random(16784).shuffle(p); s = p[:182]
if '--draw-only' in sys.argv:
    print(json.dumps(s, indent=1)); raise SystemExit
if '--from-logins' in sys.argv:
    res = json.load(open('raw/april_control_logins.json'))
    if list(res) != s:
        raise SystemExit('raw/april_control_logins.json does not match the seeded draw')
else:
    res = {}
    for u in s:
        for att in range(3):
            time.sleep(2.2)
            try: d, _ = gh.get('/search/issues?' + urllib.parse.urlencode({'q': f'author:{u} type:pr', 'per_page': 1}))
            except Exception: d = {'_error': 'exc'}
            if d.get('_error') in (403, 429, 'exc'): time.sleep(30); continue
            break
        res[u] = d.get('_error') or 200
        if res[u] == 422:
            try: d2, _ = gh.get('/users/' + u); res[u] = ('422', d2.get('_error') or 'user-exists')
            except Exception: res[u] = ('422', 'exc')
        os.makedirs('raw', exist_ok=True); json.dump(res, open('raw/april_control_logins.json', 'w'))
def lab(v):
    if v == 200: return 'ok'
    if isinstance(v, list) and v[0] == '422': return '422 user-exists' if v[1] == 'user-exists' else f'422 users-{v[1]}'
    return f'error {v}'
pub = {f'a{i + 1:03d}': lab(res[u]) for i, u in enumerate(sorted(res))}
c = {v: list(pub.values()).count(v) for v in sorted(set(pub.values()))}
json.dump({'eligible': len(pool), 'drawn': len(s), 'seed': 16784, 'counts': c, 'per_account': pub},
          open('out/april_control.json', 'w'), indent=1, sort_keys=True)
print(len(pool), 'eligible', len(s), 'probed', c)
