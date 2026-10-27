"""Collector for test-plan.md. Resumable: every search call is logged to raw/calls.jsonl, rows appended to JSONL.

Stages: tag (tagline PRs) -> miners (all PRs by M, window split <1000) -> baseline (H1) -> counts (H2).
Rows keep public PR metadata only (no bodies except the tagline flag).
"""
import json, os, random, sys, time, urllib.parse
from datetime import datetime, timedelta, timezone
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import gh

W0, W1 = '2025-04-01T00:00:00Z', '2026-10-12T23:59:59Z'
TAG = 'Contribution by Gittensor'
CALLS = 'raw/calls.jsonl'
SLEEP = 2.2
MAX_CALLS = 4000
_done = {}
if os.path.exists(CALLS):
    for l in open(CALLS):
        r = json.loads(l)
        if r.get('ok'): _done[r['key']] = r
_n = [len(_done)]


def search(q, page=1, sort=None, order=None):
    """One search call; returns (items, total_count, incomplete). Cached by key in calls.jsonl."""
    key = f'{q}|p{page}|{sort}|{order}'
    if key in _done and 'items_file' not in _done[key]:
        r = _done[key]
        return r['items'], r['total_count'], r['incomplete']
    if _n[0] >= MAX_CALLS:
        raise SystemExit('MAX_CALLS reached')
    params = {'q': q, 'per_page': 100, 'page': page}
    if sort: params.update(sort=sort, order=order or 'desc')
    for attempt in range(4):
        time.sleep(SLEEP)
        try:
            d, h = gh.get('/search/issues?' + urllib.parse.urlencode(params))
        except (OSError, TimeoutError) as e:  # AMENDMENT-02: DNS/connection errors retry (URLError is an OSError)
            d, h = {'_error': f'net:{type(e).__name__}'}, {}
            time.sleep(30)
        _n[0] += 1
        if '_error' not in d:
            break
        if d['_error'] in (403, 429):
            time.sleep(60)
    ok = '_error' not in d
    items = [slim(i) for i in d.get('items', [])] if ok else []
    rec = {'key': key, 'q': q, 'page': page, 'ok': ok, 'err': d.get('_error'), 'total_count': d.get('total_count'),
           'incomplete': d.get('incomplete_results'), 'items': items,
           'at': datetime.now(timezone.utc).isoformat(timespec='seconds')}
    with open(CALLS, 'a') as f:
        f.write(json.dumps(rec) + '\n')
    if ok:
        _done[key] = rec
    return items, d.get('total_count'), d.get('incomplete_results')


def slim(i):
    pr = i.get('pull_request') or {}
    return {'repo': i['repository_url'].split('/repos/')[1], 'number': i['number'],
            'author': (i.get('user') or {}).get('login'), 'author_type': (i.get('user') or {}).get('type'),
            'assoc': i.get('author_association'), 'created_at': i['created_at'], 'closed_at': i.get('closed_at'),
            'merged_at': pr.get('merged_at'), 'state': i.get('state'), 'draft': i.get('draft'),
            'tagline': TAG in (i.get('body') or '')}


def iso(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def p(s):
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)


def all_in(base, a=W0, b=W1, depth=0):
    """All results of `base created:a..b`, splitting the window until each slice < 1000."""
    q = f'{base} created:{a}..{b}'
    items, tot, inc = search(q)
    if tot is None:
        return []
    if tot >= 1000 and depth < 12:
        mid = p(a) + (p(b) - p(a)) / 2
        return all_in(base, a, iso(mid), depth + 1) + all_in(base, iso(mid + timedelta(seconds=1)), b, depth + 1)
    out = list(items)
    for page in range(2, min(10, (tot + 99) // 100) + 1):
        out += search(q, page)[0]
    return out


def append(path, rows):
    with open(path, 'a') as f:
        for r in rows:
            f.write(json.dumps(r) + '\n')


def load(path):
    return [json.loads(l) for l in open(path)] if os.path.exists(path) else []


def stage_tag():
    if os.path.exists('raw/tag_prs.jsonl'):
        return
    rows = all_in(f'"{TAG}" type:pr')
    append('raw/tag_prs.jsonl', rows)
    print('tag rows', len(rows), flush=True)


def miners():
    api = {m['githubUsername'] for m in json.load(open('raw/api_miners.json')) if m.get('githubUsername')}
    tag = {r['author'] for r in load('raw/tag_prs.jsonl') if r['author'] and not r['author'].endswith('[bot]')}
    low = {y.lower() for y in api}
    return sorted(api), sorted(x for x in tag if x.lower() not in low)


def stage_miners():
    api, tag_only = miners()
    done = {l.strip() for l in open('raw/miners_done.txt')} if os.path.exists('raw/miners_done.txt') else set()
    for u in api + tag_only:
        if u in done:
            continue
        rows = all_in(f'author:{u} type:pr')
        append('raw/miner_prs.jsonl', rows)
        with open('raw/miners_done.txt', 'a') as f:
            f.write(u + '\n')
        print('miner', u, len(rows), 'calls', _n[0], flush=True)


def frame():
    reg = json.load(open('out/registry.json'))
    api, tag_only = miners()
    M = {u.lower() for u in api + tag_only}
    first = {r.lower() for r in reg['first_list']}
    iv = {r.lower(): v for r, v in reg['intervals'].items()}
    def indep(repo):
        return repo.lower() in first and repo.split('/')[0].lower() not in M
    def eligible(repo, created):
        return any(a <= created and (b is None or created < b) for a, b in iv.get(repo.lower(), []))
    rows = {}
    for r in load('raw/miner_prs.jsonl'):
        if r['author'] and r['author'].lower() in M and not r['author'].endswith('[bot]'):
            rows[(r['repo'].lower(), r['number'])] = r
    return reg, M, iv, indep, eligible, list(rows.values())


T1 = '2026-04-09T21:18:56Z'
T2 = '2026-05-12T20:43:25Z'


def wins(t):
    t = p(t); d = timedelta(days=32); s = timedelta(seconds=1)
    return {'prepre': (iso(t - 2 * d), iso(t - d - s)), 'pre': (iso(t - d), iso(t - s)), 'post': (iso(t), iso(t + d - s))}


def decided90(r):
    if r['state'] != 'closed' or not r['closed_at']:
        return False
    return p(r['closed_at']) - p(r['created_at']) <= timedelta(days=90)


def stage_baseline():
    reg, M, iv, indep, eligible, rows = frame()
    dec = {}
    for r in rows:
        if indep(r['repo']) and eligible(r['repo'], r['created_at']) and r['created_at'] < T1 and not r.get('draft') \
                and r['assoc'] not in ('OWNER', 'MEMBER', 'COLLABORATOR') and decided90(r):
            dec[r['repo'].lower()] = dec.get(r['repo'].lower(), 0) + 1
    repos = sorted(k for k, v in dec.items() if v >= 3)
    if len(repos) > 400:
        repos = sorted(random.Random(16784).sample(repos, 400))
    json.dump(repos, open('out/baseline_repos.json', 'w'), indent=1)
    for repo in repos:
        items, tot, inc = search(f'repo:{repo} type:pr is:closed created:2025-04-01T00:00:00Z..2025-09-27T23:59:59Z', 1, 'created', 'desc')
        append('raw/baseline_pre_prs.jsonl', [dict(x, _repo_key=repo) for x in items])
        a = iv[repo][0][0]
        b = min(iv[repo][0][1] or T1, T1)
        items, tot, inc = search(f'repo:{repo} type:pr is:closed created:{a}..{b}', 1, 'created', 'desc')
        append('raw/baseline_in_prs.jsonl', [dict(x, _repo_key=repo) for x in items])
    print('baseline repos', len(repos), 'calls', _n[0], flush=True)


def stage_counts():
    reg, M, iv, indep, eligible, rows = frame()
    for cut, t, groups in (('cut1', T1, ('dropped', 'stayed')), ('cut2', T2, ('dropped',))):
        w = wins(t)
        for g in groups:
            repos_g = {r.lower() for r in reg[cut][g] if indep(r)}
            pre_repos = sorted({r['repo'].lower() for r in rows if r['repo'].lower() in repos_g
                                and w['pre'][0] <= r['created_at'] <= w['pre'][1]})
            json.dump({'windows': w, 'repos': pre_repos}, open(f'out/{cut}_{g}_count_repos.json', 'w'), indent=1)
            for repo in pre_repos:
                for lab, (a, b) in w.items():
                    search(f'repo:{repo} type:pr created:{a}..{b}')
                if cut == 'cut1' and g == 'dropped':
                    items, tot, inc = search(f'repo:{repo} gittensor created:<{t}')
                    append('raw/ban_screen.jsonl', [dict(x, _repo_key=repo, _total=tot) for x in items] or [{'_repo_key': repo, '_total': tot}])
            print(cut, g, 'count repos', len(pre_repos), 'calls', _n[0], flush=True)


if __name__ == '__main__':
    stages = sys.argv[1:] or ['tag', 'miners', 'baseline', 'counts']
    for s in stages:
        globals()['stage_' + s]()
    with open('raw/RUN-RECEIPT.json', 'w') as f:
        json.dump({'finished': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'calls_this_process': _n[0],
                   'stages': stages}, f)
    print('DONE calls', _n[0])
