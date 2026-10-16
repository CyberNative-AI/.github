import random
from rdkit import Chem, rdBase
from rdkit.Chem import inchi

smi = "COc1ccc(C(=O)/C=C/C2=C/C(=C/NC(C)C)C(=O)c3ccc4c(C)cc(=O)oc4c32)cc1"  # CHEMBL1290711
m = Chem.MolFromSmiles(smi)
rng = random.Random(0)
seen = {}
for _ in range(500):
    order = list(range(m.GetNumAtoms()))
    rng.shuffle(order)
    s = Chem.MolToSmiles(Chem.RenumberAtoms(m, order))
    seen[s] = seen.get(s, 0) + 1

print(rdBase.rdkitVersion)
for s, n in seen.items():
    fix = "fixpoint" if Chem.CanonSmiles(s) == s else "not a fixpoint"
    print(n, s, fix, inchi.MolToInchiKey(Chem.MolFromSmiles(s)))
