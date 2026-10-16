#!/usr/bin/env python3
"""Run the note's grep pattern over every collected in-scope file (after count.py collect) and compare it
with the frontmatter classification. python3 grep_check.py"""
import json, re, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import count
PATTERN = re.compile(r'Claude Opus (4\.8|5)([^.0-9]|$)|GPT-5\.6 Terra', re.M)
d = json.load(open(count.DATA + '/collected.json'))
scope = [i for i in d['items'] if count.SCOPE.search(i['path'])]
hits = pinned = missed = 0
for it in scope:
    text = open(f"{count.DATA}/blobs/{it['sha']}", encoding='utf-8', errors='replace').read()
    models = count.frontmatter_models(text) or []
    is_pinned = any(count.base(x)[0] in count.RETIRING and count.base(x)[1] in (None, 'copilot') for x in models)
    hit = bool(PATTERN.search(text))
    hits += hit; pinned += is_pinned; missed += is_pinned and not hit
print(json.dumps({'files_in_scope': len(scope), 'pattern_hits': hits, 'pinned': pinned, 'pinned_missed_by_pattern': missed,
                  'hits_not_pinned': hits - (pinned - missed)}, indent=1))
