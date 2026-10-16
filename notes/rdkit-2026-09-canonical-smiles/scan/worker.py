"""Worker: compute per-molecule outputs for one RDKit version on one chunk.

usage: python worker.py MODE IN_TSV OUT_JSONL
MODE: A  canonical SMILES (isomeric + flat) and SymmSSSR ring count, timing
      B  A + renumbering invariance (5 seeded permutations, legacy and new stereo perception),
         InChIKey, Morgan r2/2048 on-bit hash
      T  canonical tautomer (MolStandardize TautomerEnumerator defaults)
Env RDK_USE_LEGACY_RING_FINDING is read by RDKit itself (2026.09+); recorded, never set here.
"""
import hashlib
import json
import os
import random
import sys
import time

from rdkit import Chem, RDLogger, rdBase
from rdkit.Chem import inchi

RDLogger.DisableLog("rdApp.*")
K = 5


def perms(n, cid):
    r = random.Random(f"14054:{cid}")
    out = []
    for _ in range(K):
        p = list(range(n))
        r.shuffle(p)
        out.append(p)
    return out


def canon_set(m, ps):
    s = {Chem.MolToSmiles(m)}
    for p in ps:
        s.add(Chem.MolToSmiles(Chem.RenumberAtoms(m, p)))
    return s


def idem(c):
    """canonical output re-read and re-written gives the same string (under the current perception)"""
    m = Chem.MolFromSmiles(c)
    return m is not None and Chem.MolToSmiles(m) == c


def main():
    mode, src, dst = sys.argv[1:4]
    fpg = None
    taut = None
    if mode == "B":
        from rdkit.Chem import rdFingerprintGenerator
        fpg = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    if mode == "T":
        from rdkit.Chem.MolStandardize import rdMolStandardize
        taut = rdMolStandardize.TautomerEnumerator()
    with open(src, encoding="utf-8") as f, open(dst, "w", encoding="utf-8") as o:
        for line in f:
            cid, smi = line.rstrip("\n").split("\t")
            t0 = time.perf_counter()
            rec = {"id": cid}
            Chem.SetUseLegacyStereoPerception(True)
            m = Chem.MolFromSmiles(smi)
            if m is None:
                rec["err"] = "parse"
            else:
                try:
                    if mode in ("A", "B"):
                        rec["iso"] = Chem.MolToSmiles(m)
                        rec["flat"] = Chem.MolToSmiles(m, isomericSmiles=False)
                        rec["nsymm"] = len(Chem.GetSymmSSSR(m))
                        rec["nri"] = m.GetRingInfo().NumRings()
                        rec["idem"] = idem(rec["iso"])
                    if mode == "B":
                        ps = perms(m.GetNumAtoms(), cid)
                        rec["n_legacy"] = len(canon_set(m, ps))
                        rec["ikey"] = inchi.MolToInchiKey(m)
                        rec["ikey_rt"] = inchi.MolToInchiKey(Chem.MolFromSmiles(rec["iso"]))
                        bits = list(fpg.GetFingerprint(m).GetOnBits())
                        rec["fp"] = hashlib.sha1(",".join(map(str, bits)).encode()).hexdigest()[:16]
                        Chem.SetUseLegacyStereoPerception(False)
                        m2 = Chem.MolFromSmiles(smi)
                        cs = canon_set(m2, ps)
                        rec["n_new"] = len(cs)
                        rec["iso_new"] = Chem.MolToSmiles(m2)
                        rec["ikey_new"] = inchi.MolToInchiKey(m2)
                        rec["idem_new"] = idem(rec["iso_new"])
                        rec["ikey_rt_new"] = inchi.MolToInchiKey(Chem.MolFromSmiles(rec["iso_new"]))
                        Chem.SetUseLegacyStereoPerception(True)
                    if mode == "T":
                        rec["taut"] = Chem.MolToSmiles(taut.Canonicalize(m))
                except Exception as e:  # recorded, never dropped
                    rec["err"] = f"{type(e).__name__}: {str(e)[:120]}"
                    Chem.SetUseLegacyStereoPerception(True)
            rec["ms"] = round((time.perf_counter() - t0) * 1000, 2)
            o.write(json.dumps(rec, sort_keys=True) + "\n")
    meta = {"rdkit": rdBase.rdkitVersion, "env_legacy_ring": os.environ.get("RDK_USE_LEGACY_RING_FINDING")}
    with open(dst + ".meta", "w", encoding="utf-8") as o:
        json.dump(meta, o, sort_keys=True)


if __name__ == "__main__":
    main()
