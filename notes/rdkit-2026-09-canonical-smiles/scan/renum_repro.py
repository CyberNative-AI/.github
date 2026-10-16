"""Post-hoc: distinct canonical SMILES of the renumbering-variant molecules (seeded permutations) + idempotence."""
import json, random, sys
from rdkit import Chem, rdBase
from rdkit.Chem import inchi
out = {"rdkit": rdBase.rdkitVersion}
for cid, smi in [("CHEMBL1290711", "COc1ccc(C(=O)/C=C/C2=C/C(=C/NC(C)C)C(=O)c3ccc4c(C)cc(=O)oc4c32)cc1"),
                 ("CHEMBL1289158", "Cc1ccc(C(=O)/C=C/C2=C/C(=C/NC(C)C)C(=O)c3ccc4c(C)cc(=O)oc4c32)c(C)c1")]:
    m = Chem.MolFromSmiles(smi); s = {}
    r = random.Random(f"14054:{cid}"); P = []
    for _ in range(5):
        p = list(range(m.GetNumAtoms())); r.shuffle(p); P.append(p)
    r = random.Random(0)
    for _ in range(500):
        p = list(range(m.GetNumAtoms())); r.shuffle(p); P.append(p)
    for i, p in enumerate(P):
        c = Chem.MolToSmiles(Chem.RenumberAtoms(m, p)); s[c] = s.get(c, 0) + 1
        if i < 5: out.setdefault(cid + "_frozen_perms", []).append(c)
    out[cid] = {"distinct": s, "ikeys": sorted({inchi.MolToInchiKey(Chem.MolFromSmiles(c)) for c in s}),
                "fixpoints": {c: Chem.CanonSmiles(c) == c for c in s}}
print(json.dumps(out, indent=1))
