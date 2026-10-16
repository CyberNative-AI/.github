# keys.py: one "<name>\t<canonical SMILES>" line per input line "<SMILES> <name>"
import sys
from rdkit import Chem

for line in sys.stdin:
    smi, name = line.split()[:2]
    m = Chem.MolFromSmiles(smi)
    print(name, Chem.MolToSmiles(m) if m else "PARSE_FAIL", sep="\t")
