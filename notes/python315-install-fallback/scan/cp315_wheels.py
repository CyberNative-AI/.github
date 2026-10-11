"""Classify the latest release of top PyPI projects by what CPython 3.15 (Linux x86_64) can install without a build.
usage: python3 -I cp315_wheels.py TOP_JSON OUT_TSV [N]
Classes: pure (py3/py2.py3 none-any), abi3 (cp3X-abi3 manylinux x86_64, X<=15), cp315 (cp315 manylinux x86_64),
 older_only (only cpXY<315 binary wheels => sdist build or failure on 3.15), sdist_only, no_files, error."""
import json,sys,re,urllib.request,concurrent.futures as cf
top=json.load(open(sys.argv[1])); rows=top['rows'] if 'rows' in top else top
names=[r['project'] for r in rows][:int(sys.argv[3]) if len(sys.argv)>3 else 3000]
def cls(name):
    try:
        d=json.load(urllib.request.urlopen(urllib.request.Request('https://pypi.org/pypi/%s/json'%name,headers={'User-Agent':'cap315-scan'}),timeout=60))
    except Exception as e: return name,'','error',repr(e)[:80],''
    v=d['info']['version']; files=d.get('urls',[]); rp=d['info'].get('requires_python') or ''
    if not files: return name,v,'no_files','',rp
    whl=[f['filename'] for f in files if f['filename'].endswith('.whl')]
    if any(w.endswith('-none-any.whl') for w in whl): return name,v,'pure','',rp
    tags=set()
    for w in whl:
        m=re.match(r'.+-(?P<py>[^-]+)-(?P<abi>[^-]+)-(?P<plat>[^-]+)\.whl$',w)
        if m and 'x86_64' in m['plat'] and ('linux' in m['plat']): tags.add((m['py'],m['abi']))
    if any(py=='cp315' and abi in ('cp315','none') for py,abi in tags): return name,v,'cp315','',rp
    if any(abi=='abi3' for py,abi in tags): return name,v,'abi3','',rp
    if any(abi=='none' and py.startswith('py3') for py,abi in tags): return name,v,'pure','platform',rp
    if tags: return name,v,'older_only',' '.join(sorted(p for p,a in tags))[-60:],rp
    if whl: return name,v,'no_linux_x86_wheel',whl[0][-60:],rp
    return name,v,'sdist_only','',rp
with cf.ThreadPoolExecutor(12) as ex, open(sys.argv[2],'w') as o:
    o.write('rank\tproject\tversion\tclass\tdetail\trequires_python\n')
    for i,r in enumerate(ex.map(cls,names),1): o.write('%d\t%s\n'%(i,'\t'.join(r)))
