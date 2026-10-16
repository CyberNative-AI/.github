"""Post-hoc: canonical-SMILES uniqueness for molecules with double-bond stereo.
usage: python dbscan.py IN_TSV OUT_JSONL   (input rows = chembl_id \t smiles)
Per molecule: 10 seeded atom renumberings (seed 'db:<id>') + original order; record the
distinct canonical strings (capped at 4) and whether each is a fixpoint of MolToSmiles(MolFromSmiles(.)).
"""
import json, random, sys, time
from rdkit import Chem, RDLogger, rdBase
RDLogger.DisableLog("rdApp.*")
src, dst = sys.argv[1:3]
with open(src, encoding="utf-8") as f, open(dst, "w", encoding="utf-8") as o:
    for line in f:
        cid, smi = line.rstrip("\n").split("\t")
        t0 = time.perf_counter(); rec = {"id": cid}
        m = Chem.MolFromSmiles(smi)
        if m is None:
            rec["err"] = "parse"
        else:
            try:
                r = random.Random(f"db:{cid}"); s = {Chem.MolToSmiles(m)}
                for _ in range(10):
                    p = list(range(m.GetNumAtoms())); r.shuffle(p)
                    s.add(Chem.MolToSmiles(Chem.RenumberAtoms(m, p)))
                rec["n"] = len(s)
                if len(s) > 1:
                    rec["strings"] = sorted(s)[:4]
                    rec["fix"] = [Chem.CanonSmiles(c) == c for c in rec["strings"]]
            except Exception as e:
                rec["err"] = f"{type(e).__name__}: {str(e)[:120]}"
        rec["ms"] = round((time.perf_counter() - t0) * 1000, 2)
        o.write(json.dumps(rec, sort_keys=True) + "\n")
with open(dst + ".meta", "w", encoding="utf-8") as o:
    json.dump({"rdkit": rdBase.rdkitVersion}, o)
