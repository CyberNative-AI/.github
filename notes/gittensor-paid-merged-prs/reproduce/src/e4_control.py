"""AMENDMENT-01 E4: share of search-hidden logins among up to 182 outside authors from the pre-program baseline (seed 16784).

python3 src/e4_control.py               draw the sample, probe each login, write raw/e4_control_logins.json + out/e4_control.json
python3 src/e4_control.py --draw-only   print the drawn sample (offline)
python3 src/e4_control.py --from-logins check an existing raw/e4_control_logins.json against the draw, rewrite out/e4_control.json (offline)

out/e4_control.json replaces each login with its position in the sorted sample (c001..c182); values are unchanged.
"""
import json, os, random, sys, time, urllib.parse
sys.path.insert(0, 'src'); import gh
from collect import frame, load
reg, M, *_ = frame()
auth = sorted({b['author'] for b in load('raw/baseline_pre_prs.jsonl') if b['author'] and b['author'].lower() not in M
               and not b['author'].endswith('[bot]') and b.get('author_type') != 'Bot'
               and b['assoc'] in ('NONE', 'FIRST_TIMER', 'FIRST_TIME_CONTRIBUTOR', 'CONTRIBUTOR')})
s = sorted(random.Random(16784).sample(auth, min(182, len(auth))))
if '--draw-only' in sys.argv:
    print(json.dumps(s, indent=1)); raise SystemExit
if '--from-logins' in sys.argv:
    out = json.load(open('raw/e4_control_logins.json'))
    if sorted(out) != s:
        raise SystemExit('raw/e4_control_logins.json does not match the seeded draw')
else:
    out = {}
    for u in s:
        time.sleep(2.2)
        d, _ = gh.get('/search/issues?per_page=1&q=' + urllib.parse.quote(f'author:{u} type:pr'))
        out[u] = d.get('_error') or 'ok'
    json.dump(out, open('raw/e4_control_logins.json', 'w'), indent=1, sort_keys=True)
pub = {f'c{i + 1:03d}': out[u] for i, u in enumerate(sorted(out))}
json.dump(pub, open('out/e4_control.json', 'w'), indent=1, sort_keys=True)
print(len(auth), 'eligible', len(s), 'probed', sum(v == 422 for v in out.values()), 'x 422', sum(v not in ('ok', 422) for v in out.values()), 'other err')
