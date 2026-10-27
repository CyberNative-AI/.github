"""Removal windows from the second run's repo-wide pulls -> out/removal_windows.json (per repo, both frames, both cuts).

python3 src/removal_windows.py      (after the four pull.py runs into raw/removal/, see README.md)

Exploratory: the frames below were defined after the first run's results, when the second run found that author:
search misses 33 registered accounts whose PRs repo-wide search still returns.

- complete frame: PRs whose author is a registered miner (raw/api_miners.json), any author of a tagline PR found by the
  collector (raw/tag_prs.jsonl), or any author of a tagline PR in the pulled windows.
- search-visible frame: registered miners and collector tagline authors, minus every login whose author: search returned
  HTTP 422 in the collector's raw/calls.jsonl (the first run's frame).
- other: every pulled PR (bots included) minus the complete frame.
Bots (login ending [bot] or user type Bot) are never miner PRs.
"""
import json, os
from datetime import datetime, timedelta, timezone
F = '%Y-%m-%dT%H:%M:%SZ'
def P(s): return datetime.strptime(s, F).replace(tzinfo=timezone.utc)
def S(d): return d.strftime(F)
D32 = timedelta(days=32); SEC = timedelta(seconds=1)
CUTS = {'cut1': {'T': '2026-04-09T21:18:56Z', 'commit': 'faa56734', 'repos_file': 'out/cut1_dropped_count_repos.json', 'exclude': []},
        'cut2': {'T': '2026-05-12T20:43:25Z', 'commit': '73c9d034', 'repos_file': 'out/cut2_dropped_count_repos.json',
                 'exclude': ['infiniflow/ragflow']}}  # AMENDMENT-03: re-listed inside the cut-2 post window
T1_COMMITTER = '2026-04-10T16:39:31Z'  # committer date of faa56734 (#356)
RUFF = 'astral-sh/ruff'

api = {m['githubUsername'].lower() for m in json.load(open('raw/api_miners.json')) if m.get('githubUsername')}
tag_c = {json.loads(l)['author'].lower() for l in open('raw/tag_prs.jsonl') if json.loads(l).get('author')}
hidden = set()
for l in open('raw/calls.jsonl'):
    r = json.loads(l)
    if r.get('err') == 422 and r['q'].startswith('author:'):
        hidden.add(r['q'].split()[0][len('author:'):].lower())


def load(fn):
    rows, qs = {}, []
    for l in open(fn):
        r = json.loads(l)
        if '_q' in r: qs.append(r)
        else: rows[(r['repo'], r['n'])] = r
    return rows, qs


def bot(r):
    return not r['login'] or r['login'].endswith('[bot]') or r['type'] == 'Bot'


out = {'definitions': __doc__.split('\n\n', 2)[2].strip(), 'window_days': 32}
for cut, c in CUTS.items():
    t = P(c['T'])
    w = {'pre': (S(t - D32), S(t - SEC)), 'post': (S(t), S(t + D32 - SEC))}
    repos = [x for x in json.load(open(c['repos_file']))['repos'] if x not in c['exclude']]
    rows, qs = {}, []
    for lab in w:
        rr, q = load(f'raw/removal/{cut}_{lab}.jsonl')
        rows.update(rr); qs += q
    tag_w = {r['login'].lower() for r in rows.values() if r['tag'] and r['login']}
    full, vis = api | tag_c | tag_w, (api | tag_c) - hidden
    def frame_of(r):
        if bot(r): return None
        u = r['login'].lower()
        return 'vis' if u in vis else ('full' if u in full else None)
    per = {x: {k: {'all_prs': 0, 'complete': 0, 'search_visible': 0, 'other': 0} for k in w} for x in repos}
    for r in rows.values():
        k = next(k for k, (a, b) in w.items() if a <= r['created'] <= b)
        f = frame_of(r); d = per[r['repo']][k]
        d['all_prs'] += 1
        d['complete'] += f is not None
        d['search_visible'] += f == 'vis'
        d['other'] += f is None
    tot = {k: {m: sum(per[x][k][m] for x in repos) for m in ('all_prs', 'complete', 'search_visible', 'other')} for k in w}
    res = {'commit': c['commit'], 'T': c['T'], 'windows': w, 'repos_counted': len(repos), 'repos_excluded': c['exclude'],
           'queries': len(qs), 'queries_short': sum(q['total'] != q['got'] for q in qs), 'totals': tot,
           'per_repo': per}
    if cut == 'cut1':
        ex = [x for x in repos if x != RUFF]
        res['excluding_ruff'] = {k: {m: sum(per[x][k][m] for x in ex) for m in ('complete', 'search_visible')} for k in w}
        # removal dated by the committer date: pre = 32 days before it; post = from it to the end of the pulled post
        # window (19 h short of 32 days, because the pulls were made around the author date)
        t2 = P(T1_COMMITTER)
        w2 = {'pre': (S(t2 - D32), S(t2 - SEC)), 'post': (S(t2), w['post'][1])}
        v = {}
        for name, keep in (('all_repos', set(repos)), ('excluding_ruff', set(ex))):
            v[name] = {k: {'complete': 0, 'search_visible': 0} for k in w2}
            for r in rows.values():
                if r['repo'] not in keep: continue
                f = frame_of(r)
                for k, (a, b) in w2.items():
                    if a <= r['created'] <= b and f is not None:
                        v[name][k]['complete'] += 1
                        v[name][k]['search_visible'] += f == 'vis'
        res['committer_date_variant'] = {'T': T1_COMMITTER, 'windows': w2, **v}
    out[cut] = res
os.makedirs('out', exist_ok=True)
json.dump(out, open('out/removal_windows.json', 'w'), indent=1, sort_keys=True)
for cut in CUTS:
    t = out[cut]['totals']
    print(cut, 'complete', t['pre']['complete'], '->', t['post']['complete'], '| search-visible', t['pre']['search_visible'], '->',
          t['post']['search_visible'], '| other', t['pre']['other'], '->', t['post']['other'], '| short queries', out[cut]['queries_short'])
e, v = out['cut1']['excluding_ruff'], out['cut1']['committer_date_variant']
print('cut1 excl. ruff complete', e['pre']['complete'], '->', e['post']['complete'],
      '| committer date complete', v['all_repos']['pre']['complete'], '->', v['all_repos']['post']['complete'],
      '| committer date excl. ruff', v['excluding_ruff']['pre']['complete'], '->', v['excluding_ruff']['post']['complete'])
