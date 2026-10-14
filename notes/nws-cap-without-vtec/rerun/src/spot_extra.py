import sys; sys.argv=['x','../raw']
import io,contextlib
with contextlib.redirect_stdout(io.StringIO()): exec(open('src/spot_check.py').read().split("sel=random")[0])
from datetime import datetime
for k in ['PAFC.SC.Y.1594','PAFC.SC.Y.1599']:
    print(k)
    for i in sorted(ev[k],key=lambda i:datetime.fromisoformat(al[i]['sent'])):
        p=al[i];print(' ',p['sent'],p['messageType'],p['parameters']['VTEC'],p['parameters']['WMOidentifier'],p['areaDesc'][:40],p['id'][-20:])
# population: split events with only NEW roots: same AWIPS+sent among NEW roots?
c=collections.Counter()
for k in split:
    comps=collections.defaultdict(list)
    for i in ev[k]: comps[find(i)].append(i)
    roots=[min(m,key=lambda i:datetime.fromisoformat(al[i]['sent'])) for m in comps.values()]
    if any(act(r)!='NEW' for r in roots): c['chain_restart']+=1; continue
    sig={(tuple(al[r]['parameters'].get('AWIPSidentifier') or []),al[r]['sent'],tuple(al[r]['parameters'].get('WMOidentifier') or [])) for r in roots}
    c['parNEW_same_product' if len(sig)==1 else 'parNEW_multi_product']+=1
print(c)
# EXA/EXB population
ee=[p for p in al.values() if vt(p) and vt(p)[0][0] in ('EXA','EXB')]
print(len(ee),sum(1 for p in ee if not p.get('references') and not (p['parameters'].get('expiredReferences'))))
