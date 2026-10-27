"""Second-run pull: all PRs created in a window per repo via repo-wide search, bisecting windows until <1000. Writes jsonl.

python3 src/pull.py OUT.jsonl owner/repo,owner/repo,... FROM TO      (FROM/TO as YYYY-MM-DDTHH:MM:SSZ, both inclusive)

Resumable: finished repos are listed in OUT.jsonl.done; rows of an unfinished repo are dropped and pulled again.
"""
import sys, json, time, os, urllib.parse
from datetime import datetime, timedelta, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gh
F='%Y-%m-%dT%H:%M:%SZ'
def P(s): return datetime.strptime(s,F).replace(tzinfo=timezone.utc)
def S(d): return d.strftime(F)
OUT=sys.argv[1]; repos=sys.argv[2].split(','); a0,b0=sys.argv[3],sys.argv[4]
errs=[0]; calls=[0]
def call(q,page):
    for att in range(4):
        time.sleep(2.2)
        calls[0]+=1
        try: d,h=gh.get('/search/issues?'+urllib.parse.urlencode({'q':q,'per_page':100,'page':page}))
        except Exception as e:
            d,h={'_error':'exc:'+type(e).__name__},{}
        if '_error' not in d: return d
        errs[0]+=1; time.sleep(30 if d['_error'] in (403,429) else 5)
    raise SystemExit('fail '+q)
def slim(i,repo):
    pr=i.get('pull_request') or {}
    return {'repo':repo,'n':i['number'],'login':(i.get('user') or {}).get('login'),'type':(i.get('user') or {}).get('type'),'assoc':i.get('author_association'),
            'created':i['created_at'],'closed':i.get('closed_at'),'merged':pr.get('merged_at'),'state':i['state'],'draft':i.get('draft'),
            'tag':'Contribution by Gittensor' in (i.get('body') or '')}
def rng(repo,a,b,f):
    q=f'repo:{repo} type:pr created:{a}..{b}'
    d=call(q,1); tot=d['total_count']
    if d.get('incomplete_results'): print('INCOMPLETE',q,flush=True)
    if tot>1000 and P(b)-P(a)>timedelta(seconds=1):
        m=P(a)+(P(b)-P(a))/2; m=m.replace(microsecond=0)
        rng(repo,a,S(m),f); rng(repo,S(m+timedelta(seconds=1)),b,f); return
    items=d['items']; pg=1
    while len(items)<tot and pg<10:
        pg+=1; dd=call(q,pg); items+=dd['items']
        if not dd['items']: break
    for i in items: f.write(json.dumps(slim(i,repo))+'\n')
    f.write(json.dumps({'_q':q,'total':tot,'got':len(items)})+'\n'); f.flush()
DONE=OUT+'.done'
done=set(open(DONE).read().split()) if os.path.exists(DONE) else set()
if os.path.exists(OUT):  # drop rows of repos that did not finish
    keep=[l for l in open(OUT) if (json.loads(l).get('repo') or json.loads(l)['_q'].split()[0][5:]) in done]
    open(OUT,'w').writelines(keep)
with open(OUT,'a') as f:
    for r in repos:
        if r in done: continue
        rng(r,a0,b0,f); open(DONE,'a').write(r+'\n'); print(r,'calls',calls[0],'errs',errs[0],flush=True)
