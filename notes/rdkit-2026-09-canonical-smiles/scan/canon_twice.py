"""Claims check: per P1 molecule, distinct strings over 100 orderings of the ChEMBL input for MolToSmiles and for CanonSmiles(MolToSmiles)."""
import json, random, sys
from rdkit import Chem, rdBase
rows = [l.rstrip("\n").split("\t")[:2] for l in open(sys.argv[1])]
out = {"rdkit": rdBase.rdkitVersion, "rows": []}
for cid, smi in rows:
    m = Chem.MolFromSmiles(smi); rng = random.Random(cid)
    once, twice = set(), set()
    for _ in range(100):
        o = list(range(m.GetNumAtoms())); rng.shuffle(o)
        s = Chem.MolToSmiles(Chem.RenumberAtoms(m, o)); once.add(s); twice.add(Chem.CanonSmiles(s))
    out["rows"].append([cid, len(once), len(twice)])
print(json.dumps(out))
