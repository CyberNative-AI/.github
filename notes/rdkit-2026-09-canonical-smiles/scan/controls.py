"""Positive controls: known 2026.09.1 changes the harness must detect."""
import json, random
from rdkit import Chem, rdBase
out = {"rdkit": rdBase.rdkitVersion}
# 1. atom-map note: canonical=False, ignoreAtomMapNumbers=True keeps map numbers from 2026.09
m = Chem.MolFromSmiles("[CH3:1][OH:2]")
out["atommap_noncanon_ignore"] = Chem.MolToSmiles(m, canonical=False, ignoreAtomMapNumbers=True)
# 2. issue 9701 inositol under new stereo perception: two inputs, same InChI
a = "O[C@@H]1[C@H](O)[C@H](O)[C@@H](O)[C@H](O)[C@@H]1O"; b = "O[C@@H]1[C@H](O)[C@H](O)[C@H](O)[C@H](O)[C@H]1O"
for flag in (True, False):
    Chem.SetUseLegacyStereoPerception(flag)
    out[f"inositol_same_canon_legacy={flag}"] = Chem.CanonSmiles(a) == Chem.CanonSmiles(b)
    ma = Chem.MolFromSmiles(a); r = random.Random(1); s = set()
    for _ in range(5):
        p = list(range(ma.GetNumAtoms())); r.shuffle(p); s.add(Chem.MolToSmiles(Chem.RenumberAtoms(ma, p)))
    ca = Chem.CanonSmiles(a)
    out[f"inositol_a_idem_legacy={flag}"] = Chem.CanonSmiles(ca) == ca
    out[f"inositol_a_nperm_legacy={flag}"] = len(s | {Chem.MolToSmiles(ma)})
Chem.SetUseLegacyStereoPerception(True)
print(json.dumps(out, sort_keys=True))
