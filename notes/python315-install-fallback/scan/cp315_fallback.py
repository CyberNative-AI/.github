"""For projects whose latest release caps requires_python below 3.15, find what an unpinned install resolves to on CPython 3.15.0:
the highest non-yanked, non-prerelease release that has files and whose requires_python admits 3.15.0 (missing = admits).
usage: python3 -I cp315_fallback.py IN_TSV OUT_TSV"""
import json,sys,re,urllib.request,concurrent.futures as cf
from packaging.version import Version,InvalidVersion
from packaging.specifiers import SpecifierSet,InvalidSpecifier
rows=[l.rstrip('\n').split('\t') for l in open(sys.argv[1])][1:]
capped=[r for r in rows if r[5] and not SpecifierSet(r[5]).contains('3.15.0',prereleases=True)]
def ok(rp):
    if not rp: return True
    try: return SpecifierSet(rp).contains('3.15.0',prereleases=True)
    except InvalidSpecifier: return True
def fb(r):
    name=r[1]
    d=json.load(urllib.request.urlopen(urllib.request.Request('https://pypi.org/pypi/%s/json'%name,headers={'User-Agent':'cap315-scan'}),timeout=90))
    best=None
    for v,files in d['releases'].items():
        try: V=Version(v)
        except InvalidVersion: continue
        if V.is_prerelease or not files or all(f.get('yanked') for f in files): continue
        live=[f for f in files if not f.get('yanked')]
        if not ok(live[0].get('requires_python')): continue
        if best is None or V>best[0]: best=(V,live)
    if not best: return r[:4]+[r[5],'NONE','','','']
    V,live=best
    up=min(f['upload_time_iso_8601'] for f in live)[:10]
    kinds=sorted({('pure' if f['filename'].endswith('-none-any.whl') else 'wheel' if f['filename'].endswith('.whl') else 'sdist') for f in live})
    return r[:4]+[r[5],str(V),up,'+'.join(kinds),live[0].get('requires_python') or '']
with cf.ThreadPoolExecutor(8) as ex, open(sys.argv[2],'w') as o:
    o.write('rank\tproject\tlatest\tclass\tlatest_requires_python\tfallback_on_3.15\tfallback_uploaded\tfallback_files\tfallback_requires_python\n')
    for out in ex.map(fb,capped): o.write('\t'.join(out)+'\n')
