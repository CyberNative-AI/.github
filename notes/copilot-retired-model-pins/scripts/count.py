#!/usr/bin/env python3
"""Count public Copilot agent, prompt and chat mode files whose frontmatter `model:` names a model
GitHub retires on 2026-11-16 (Claude Opus 4.8, Claude Opus 5, GPT-5.6 Terra).

  GITHUB_TOKEN=... python3 count.py collect   # code search + file contents into ./data (slow: search rate limits)
  python3 count.py summarize                  # classify ./data and print summary JSON

Code search indexes default branches only, skips forks and caps each query at 1,000 results,
so the counts are lower bounds.
"""
import base64, collections, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

RETIRING = {'Claude Opus 4.8', 'Claude Opus 5', 'GPT-5.6 Terra'}
RETIRING_IDS = {'claude-opus-4.8', 'claude-opus-5', 'gpt-5.6-terra'}
QUERIES = ['"Claude Opus 4.8" path:.github', '"Claude Opus 5" path:.github', '"GPT-5.6 Terra" path:.github']
SCOPE = re.compile(r'(^|/)\.github/(agents|prompts|chatmodes)/')
DATA = 'data'

def get(path, params=None):
    url = 'https://api.github.com' + path + ('?' + urllib.parse.urlencode(params) if params else '')
    for attempt in range(5):
        req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'],
                                                   'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (403, 429) and attempt < 4:
                reset = int(e.headers.get('X-RateLimit-Reset') or time.time() + 60)
                time.sleep(max(5, min(900, reset - time.time() + 2)))
                continue
            raise

def collect():
    os.makedirs(DATA + '/blobs', exist_ok=True)
    items, totals = {}, {}
    for q in QUERIES:
        page = 1
        while True:
            d = get('/search/code', {'q': q, 'per_page': 100, 'page': page})
            time.sleep(7)
            totals.setdefault(q, d['total_count'])
            for i in d['items']:
                items.setdefault((i['repository']['full_name'], i['path']), {'repo': i['repository']['full_name'], 'path': i['path'], 'sha': i['sha']})
            if len(d['items']) < 100 or page * 100 >= min(d['total_count'], 1000):
                break
            page += 1
    for v in items.values():
        fn = f"{DATA}/blobs/{v['sha']}"
        if not os.path.exists(fn):
            open(fn, 'wb').write(base64.b64decode(get(f"/repos/{v['repo']}/git/blobs/{v['sha']}")['content']))
    json.dump({'run_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'totals': totals, 'items': list(items.values())},
              open(DATA + '/collected.json', 'w'), indent=1)

def base(name):
    """('Claude Opus 5', 'copilot') for 'Claude Opus 5 (copilot)'; vendor None when absent."""
    name = name.strip().strip('\'"').strip()
    m = re.match(r'^(.*?)\s*\(([^)]*)\)$', name)
    return (m.group(1).strip(), m.group(2).strip().lower()) if m else (name, None)

def frontmatter_models(text):
    """The `model:` value of the YAML frontmatter as a list: scalar, [inline, array] or block list."""
    t = text.replace('\r\n', '\n').lstrip('﻿')
    if not t.startswith('---'):
        return None
    end = t.find('\n---', 3)
    if end < 0:
        return None
    lines = t[3:end].split('\n')
    for i, line in enumerate(lines):
        m = re.match(r'^model\s*:\s*(.*)$', line)
        if not m:
            continue
        v = m.group(1).strip()
        rest = lines[i + 1:]
        if v == '' and rest and rest[0].strip().startswith('['):
            v, rest = rest[0].strip(), rest[1:]
        if v.startswith('['):
            while ']' not in v and rest:  # flow list over several lines
                v, rest = v + ' ' + re.sub(r'\s+#.*$', '', rest[0]).strip(), rest[1:]
            out = [x.strip().strip('\'"').strip() for x in re.sub(r'\s+#.*$', '', v).strip('[]').split(',')]
            return [x for x in out if x]
        if v == '':
            out = []
            for nxt in rest:
                m2 = re.match(r'^\s*-\s*(.+)$', nxt)
                if m2:
                    out.append(m2.group(1).strip())
                elif nxt.strip():
                    break
            return out
        return [re.sub(r'\s+#.*$', '', v)]
    return None

def summarize():
    d = json.load(open(DATA + '/collected.json'))
    rows = []
    for it in d['items']:
        if not SCOPE.search(it['path']):
            continue
        models = frontmatter_models(open(f"{DATA}/blobs/{it['sha']}", encoding='utf-8', errors='replace').read())
        if not models:
            continue
        names = [base(x) for x in models]
        retiring = [n for n in names if n[0] in RETIRING and n[1] in (None, 'copilot')]
        if not retiring:
            continue
        # "No fallback": every listed name is one of the three (display name or model ID form).
        # Any other listed name counts as a fallback; we do not check that it still exists.
        fallback = any(n[0] not in RETIRING and n[0].lower() not in RETIRING_IDS for n in names)
        rows.append({'repo': it['repo'], 'models': models, 'retiring': sorted({n[0] for n in retiring}), 'no_fallback': not fallback,
                     'dir': SCOPE.search(it['path']).group(2)})
    nofb = [r for r in rows if r['no_fallback']]
    per_model = {m: {'files': sum(m in r['retiring'] for r in rows), 'files_no_fallback': sum(m in r['retiring'] for r in nofb)} for m in sorted(RETIRING)}
    out = {'search_run_utc': d['run_utc'], 'search_totals': {q: d['totals'][q] for q in QUERIES if q in d['totals']},
           'files': len(rows), 'repos': len({r['repo'] for r in rows}), 'owners': len({r['repo'].split('/')[0] for r in rows}),
           'files_no_fallback': len(nofb), 'repos_no_fallback': len({r['repo'] for r in nofb}),
           'by_dir': dict(collections.Counter(r['dir'] for r in rows)), 'per_model': per_model,
           'model_values': dict(collections.Counter(base(x)[0] + (f" ({base(x)[1]})" if base(x)[1] else '') for r in rows for x in r['models'] if base(x)[0] in RETIRING))}
    print(json.dumps(out, indent=1))

if __name__ == '__main__':
    {'collect': collect, 'summarize': summarize}[sys.argv[1]]()
