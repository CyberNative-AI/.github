import json,glob,re,random,collections,sys
R=sys.argv[1]
al={}
for f in sorted(glob.glob(R+'/page-*.json')):
    for ft in json.load(open(f))['features']:
        p=ft['properties']
        if p.get('status')=='Actual': al[p['id']]=p
V=re.compile(r'^/O\.([A-Z]{3})\.([A-Z]{4})\.([A-Z]{2})\.([A-Z])\.(\d{4})\.')
def vt(p):
    out=[]
    for s in (p.get('parameters') or {}).get('VTEC') or []:
        m=V.match(s)
        if m: out.append((m.group(1),m.group(2)+'.'+m.group(3)+'.'+m.group(4)+'.'+m.group(5)))
    return out
def refs(p):
    r=[x['identifier'] for x in p.get('references') or []]
    for s in (p.get('parameters') or {}).get('expiredReferences') or []:
        for t in s.split():
            parts=t.split(',')
            if len(parts)>=2: r.append(parts[1])
    return r
ev=collections.defaultdict(list)
for i,p in al.items():
    v=vt(p)
    assert len(v)<=1
    for a,k in v: ev[k].append(i)
par={}
def find(x):
    while par.setdefault(x,x)!=x: par[x]=par[par[x]]; x=par[x]
    return x
for i,p in al.items():
    for r in refs(p):
        q=al.get(r)
        if q and q['event']==p['event'] and q['senderName']==p['senderName']: par[find(i)]=find(r)
def act(i): return vt(al[i])[0][0]
evald=[k for k,ids in ev.items() if len(ids)>=2 and any(act(i)=='NEW' for i in ids)]
split=sorted(k for k in evald if len({find(i) for i in ev[k]})>1)
print('evaluated',len(evald),'split',len(split),'exact',len(evald)-len(split))
sel=random.Random(135030).sample(split,20)
res=[]
for k in sel:
    comps=collections.defaultdict(list)
    for i in ev[k]: comps[find(i)].append(i)
    print('\n==',k,'alerts',len(ev[k]),'components',len(comps))
    ok_c=True; roots=[]
    for c,m in comps.items():
        m.sort(key=lambda i:al[i]['sent'] if False else al[i]['effective'] or al[i]['sent'])
        # root: earliest by sent (parse offsets)
        from datetime import datetime
        m.sort(key=lambda i:datetime.fromisoformat(al[i]['sent']))
        roots.append(m[0])
        print(' comp',len(m),'root',al[m[0]]['id'][-24:],'|',' '.join(f"{act(i)}/{al[i]['messageType'][0]}" for i in m))
    for r in sorted(roots,key=lambda i:datetime.fromisoformat(al[i]['sent'])):
        p=al[r]
        print('  ROOT',act(r),p['messageType'],p['sent'],p['parameters'].get('AWIPSidentifier'),p['parameters'].get('WMOidentifier'),'refs',len(p.get('references') or []),'expref',len((p['parameters'].get('expiredReferences') or [])),p['id'][-24:],vt(p)[0][1],'|',p['areaDesc'][:50])
    # (a) all EXA/EXB in this event
    for i in ev[k]:
        if act(i) in('EXA','EXB'):
            p=al[i]; print('  EX',act(i),p['messageType'],'refs',len(p.get('references') or []),'exprefs',len(p['parameters'].get('expiredReferences') or []))
    nr=sorted(roots,key=lambda i:datetime.fromisoformat(al[i]['sent']))
    first=nr[0]
    newroots=[r for r in nr if act(r)=='NEW']
    b=None
    if len(newroots)>=2:
        sig={(tuple(al[r]['parameters'].get('AWIPSidentifier') or []),al[r]['sent']) for r in newroots}
        b=len(sig)==1
        print('  (b) NEW roots',len(newroots),'same AWIPS+sent:',b, sig if not b else '')
    c_=len({vt(al[i])[0][1] for i in ev[k]})==1
    restart=[r for r in nr if act(r)!='NEW']
    res.append(dict(k=k,newroots=len(newroots),b=b,restart=len(restart),restart_noref=all(not al[r].get('references') and not al[r]['parameters'].get('expiredReferences') for r in restart),ex_all_noref=all(not al[i].get('references') and not al[i]['parameters'].get('expiredReferences') for i in ev[k] if act(i) in('EXA','EXB')),oneETN=c_))
print()
print(json.dumps(res,indent=0))
print('(a) all EXA/EXB checked have no refs:',all(r['ex_all_noref'] for r in res),'; restart roots no refs:',all(r['restart_noref'] for r in res))
print('(b) events with >=2 NEW roots:',sum(1 for r in res if r['b'] is not None),'all same AWIPS+sent:',all(r['b'] for r in res if r['b'] is not None))
print('(c) one key:',all(r['oneETN'] for r in res))
