"""The 33 registered accounts that author: search cannot find: counts only, no logins -> out/hidden_accounts.json.

python3 src/hidden_accounts.py      (offline; after `unsearchable.py --check-accounts` and the four pulls in README step 7)

- accounts: how many of the hidden accounts still have a /users profile (found) and how many return 404 (deleted).
- windows: per removal window (32 days before and after each cut, as in removal_windows.py), how many hidden accounts
  have at least one PR there, their PR count and merge state; per cut (pre or post) and across both cuts.
Merge state is as of the pull: merged (merged_at set), closed (closed, not merged), open. Bots are not counted.
"""
import json
hid = json.load(open('raw/unsearchable_accounts.json'))
if any('users_login' not in v for v in hid.values()):
    raise SystemExit('run src/unsearchable.py --check-accounts first')
low = {u.lower() for u in hid}
acc = {'hidden': len(hid), 'profile_found': sum(v['users_login'] == 'found' for v in hid.values()),
       'deleted_404': sum(v['users_login'] == 404 for v in hid.values())}
acc['other'] = acc['hidden'] - acc['profile_found'] - acc['deleted_404']
EXCL = {'cut2': {'infiniflow/ragflow'}}


def prs(cut, lab):
    keep = set(json.load(open(f'out/{cut}_dropped_count_repos.json'))['repos']) - EXCL.get(cut, set())
    return [r for r in map(json.loads, open(f'raw/removal/{cut}_{lab}.jsonl')) if '_q' not in r and r['repo'] in keep
            and r['login'] and not r['login'].endswith('[bot]') and r['type'] != 'Bot' and r['login'].lower() in low]


def summ(rs):
    return {'accounts': len({r['login'].lower() for r in rs}), 'prs': len(rs),
            'merged': sum(bool(r['merged']) for r in rs),
            'closed_unmerged': sum(r['state'] == 'closed' and not r['merged'] for r in rs),
            'open': sum(r['state'] == 'open' for r in rs)}


W = {(c, l): prs(c, l) for c in ('cut1', 'cut2') for l in ('pre', 'post')}
win = {f'{c}_{l}': summ(rs) for (c, l), rs in W.items()}
for c in ('cut1', 'cut2'):
    win[f'{c}_pre_or_post'] = summ(W[c, 'pre'] + W[c, 'post'])
    a = {r['login'].lower() for r in W[c, 'pre']} & {r['login'].lower() for r in W[c, 'post']}
    win[f'{c}_pre_and_post_accounts'] = len(a)
s1 = {r['login'].lower() for c in [('cut1', 'pre'), ('cut1', 'post')] for r in W[c]}
s2 = {r['login'].lower() for c in [('cut2', 'pre'), ('cut2', 'post')] for r in W[c]}
win['either_cut_accounts'] = len(s1 | s2)
win['both_cuts_accounts'] = len(s1 & s2)
json.dump({'definitions': __doc__.split('\n\n', 2)[2].strip(), 'accounts': acc, 'windows': win},
          open('out/hidden_accounts.json', 'w'), indent=1, sort_keys=True)
print('hidden', acc)
for k, v in win.items(): print(k, v)
