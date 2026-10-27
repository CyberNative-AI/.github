"""Registry intervals per repo from the 237 list commits (fixed frame; no outcomes)."""
import json
CUT1 = 'faa56734f3'; CUT2 = '73c9d0347a'
cs = json.load(open('raw/whitelist_commits.json'))[::-1]  # oldest first
state, prev_date, iv, bad, snaps = set(), None, {}, [], []
for c in cs:
    try:
        cur = set(json.load(open(f"raw/wl/{c['sha']}.json")))
    except json.JSONDecodeError:
        bad.append(c['sha']); cur = state  # carry previous state forward
    for r in cur - state: iv.setdefault(r, []).append([c['date'], None])
    for r in state - cur: iv[r][-1][1] = c['date']
    snaps.append((c['sha'], c['date'], cur)); state = cur
first = snaps[0][2]
def around(prefix):
    i = next(k for k, s in enumerate(snaps) if s[0].startswith(prefix))
    return snaps[i - 1][2], snaps[i][2], snaps[i][1]
b1, a1, d1date = around(CUT1); b2, a2, d2date = around(CUT2)
out = {'bad_json_commits': bad, 'n_commits': len(cs), 'first_list': sorted(first),
       'cut1': {'date': d1date, 'dropped': sorted(b1 - a1), 'stayed': sorted(a1)},
       'cut2': {'date': d2date, 'dropped': sorted(b2 - a2), 'stayed': sorted(a2)},
       'intervals': iv}
json.dump(out, open('out/registry.json', 'w'), indent=1, sort_keys=True)
print('repos ever', len(iv), 'first', len(first), 'bad', bad)
print('cut1', d1date, 'dropped', len(b1 - a1), 'stayed', len(a1), '| cut2', d2date, 'dropped', len(b2 - a2), 'stayed', len(a2))
print('repos with >1 interval', sum(len(v) > 1 for v in iv.values()))
