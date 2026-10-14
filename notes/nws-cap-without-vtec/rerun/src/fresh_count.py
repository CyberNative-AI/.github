import json,glob,re,sys,collections
def load(d):
    al={}; n=0
    for f in sorted(glob.glob(d+'/page-*.json')):
        for ft in json.load(open(f))['features']:
            n+=1; p=ft['properties']
            if p.get('status')=='Actual': al[p['id']]=p
    return al,n
V=re.compile(r'^/O\.([A-Z]{3})\.')
def act(p):
    for s in (p.get('parameters') or {}).get('VTEC') or []:
        m=V.match(s)
        if m: return m.group(1)
def hasref(p): return bool(p.get('references')) or bool((p.get('parameters') or {}).get('expiredReferences'))
old,_=load(sys.argv[1]); new,n=load(sys.argv[2])
def tab(al):
    t=collections.Counter()
    for p in al.values():
        a=act(p)
        if a: t[(a,p['messageType'],'refs' if hasref(p) else 'norefs')]+=1
    return t
def show(name,al):
    t=tab(al); print('==',name,'Actual alerts',len(al),'with operational VTEC',sum(t.values()))
    for (a,m,r),c in sorted(t.items()): print(f'  {a:4}{m:7}{r:7}{c}')
    ex=[c for (a,m,r),c in t.items() if a in('EXA','EXB')]; nr=sum(c for (a,m,r),c in t.items() if a in('EXA','EXB') and r=='norefs')
    print('  EXA/EXB total',sum(ex),'no refs',nr)
    oth=[(a,m,r,c) for (a,m,r),c in t.items() if a not in('EXA','EXB','NEW') and r=='norefs']; print('  non-EX/NEW without refs',oth)
print('fresh rows',n,'unique actual',len(new)); ids=set(new)-set(old); print('ids not in snapshot',len(ids),'; snapshot ids absent now',len(set(old)-set(new)))
show('fresh listing (all)',new)
show('fresh-only ids (not in snapshot)',{i:new[i] for i in ids})
