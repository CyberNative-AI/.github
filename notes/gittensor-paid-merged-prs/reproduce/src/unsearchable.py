"""AMENDMENT-01/-03: registered miner logins whose `author:` search returns HTTP 422 -> raw/unsearchable_accounts.json.

python3 src/unsearchable.py                    offline, from the collector's raw/calls.jsonl
python3 src/unsearchable.py --check-accounts   also asks /users/{login} whether each account still exists

posthoc.py uses only the number of entries.
"""
import json, sys
sys.path.insert(0, 'src'); import gh
api = {m['githubUsername'] for m in json.load(open('raw/api_miners.json')) if m.get('githubUsername')}
low = {u.lower(): u for u in api}
hit = set()
for line in open('raw/calls.jsonl'):
    r = json.loads(line)
    if r.get('err') == 422 and r['q'].startswith('author:'):
        u = r['q'].split()[0][len('author:'):]
        if u.lower() in low:
            hit.add(low[u.lower()])
out = {u: {'search': 422} for u in sorted(hit)}
if '--check-accounts' in sys.argv:
    for u in out:
        d, _ = gh.get('/users/' + u)
        out[u]['users_login'] = 'found' if '_error' not in d else d['_error']
json.dump(out, open('raw/unsearchable_accounts.json', 'w'), indent=1, sort_keys=True)
print(len(api), 'registered logins', len(out), 'unsearchable')
