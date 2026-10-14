import json, random, glob, sys
from pathlib import Path
R=str(Path(__file__).resolve().parents[1])+"/"
key={u["uid"]:u for u in json.load(open(R+"adjudication/units_key.json"))}
V={}
for f in sorted(glob.glob(R+"adjudication/verdicts_*.json")): V.update(json.load(open(f)))
ITEMS=sorted(next(iter(V.values())).keys())
elig=sorted(u for u,k in key.items() if k["arm"]!="control" and k["part"]!="narration" and u!="U3972")
yes=[(u,i) for u in elig for i in ITEMS if V[u][i]["match"]]
no=[(u,i) for u in elig for i in ITEMS if not V[u][i]["match"]]
topic={(key[u]["arm"],key[u]["version"],i) for u,i in yes}
near=[c for c in no if (key[c[0]]["arm"],key[c[0]]["version"],c[1]) in topic]
far=[c for c in no if c not in set(near)]
rng=random.Random(20261014)
s=rng.sample(yes,20)
n1=rng.sample(near,12); n2=rng.sample(far,8)
cells=s+n1+n2
rng.shuffle(cells)
json.dump({"cells":cells,"strata":{"yes":sorted(s),"near":sorted(n1),"far":sorted(n2)}},open("cells_private.json","w"))
json.dump(cells,open("cells_public.json","w"))
print(len(elig),len(yes),len(no),len(near),len(far),len(set(cells)))
