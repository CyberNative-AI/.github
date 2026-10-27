"""Second-run summary of one cut's pulls (pull.py output): row, query and frame counts per window. Prints JSON, writes nothing.

python3 src/analyze_pull.py raw/removal/cut1_pre.jsonl raw/removal/cut1_post.jsonl

Frames: A = registered miners (raw/api_miners.json); B = A + tagline authors seen in the pulled window; C = A + all
tagline authors from the collector (raw/tag_prs.jsonl); D = all of these (the complete frame).
"""
import json, sys
from collections import Counter
api={m['githubUsername'].lower() for m in json.load(open('raw/api_miners.json')) if m.get('githubUsername')}
tagonly={json.loads(l)['author'].lower() for l in open('raw/tag_prs.jsonl') if json.loads(l).get('author')}
def load(fn):
    rows=[];qs=[]
    for l in open(fn):
        r=json.loads(l)
        (qs if '_q' in r else rows).append(r)
    return rows,qs
out={}
for lab,fn in (('pre',sys.argv[1]),('post',sys.argv[2])):
    rows,qs=load(fn)
    ded={(r['repo'],r['n']):r for r in rows}
    bad=[q for q in qs if q['total']!=q['got']]
    tag_auth={r['login'].lower() for r in ded.values() if r['tag'] and r['login']}
    nonbot=[r for r in ded.values() if r['login'] and not r['login'].endswith('[bot]') and r['type']!='Bot']
    out[lab]=dict(rows=len(ded),queries=len(qs),short=len(bad),nonbot=len(nonbot),
      A_api=sum(r['login'].lower() in api for r in nonbot),
      B_api_or_tag_in_window=sum(r['login'].lower() in api|tag_auth for r in nonbot),
      C_api_or_collector_tag=sum(r['login'].lower() in api|tagonly for r in nonbot),
      D_all=sum(r['login'].lower() in api|tag_auth|tagonly for r in nonbot),
      authors_D=len({r['login'].lower() for r in nonbot if r['login'].lower() in api|tag_auth|tagonly}),
      tag_prs=sum(r['tag'] for r in ded.values()), tag_authors_not_in_api=len(tag_auth-api))
    out[lab]['by_repo_D']=Counter(r['repo'] for r in nonbot if r['login'].lower() in api|tag_auth|tagonly).most_common()
    out[lab]['total_by_repo']=sum(1 for _ in ded)
print(json.dumps(out,indent=1))
