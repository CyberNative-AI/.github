# Will upgrading RDKit to 2026.09 change your canonical SMILES keys?

RDKit 2026.09.1 came out on 3 October 2026. If your registration, deduplication or caching step uses
`Chem.MolToSmiles` as a key, the useful question before you move the pin is which keys change.

We canonicalized all 2,897,819 ChEMBL 37 structures with four RDKit releases (PyPI wheels, Linux, CPython 3.12) and
compared the output.

**Short answer: 2026.03 → 2026.09 changed the canonical SMILES of 202 molecules (0.007%). That makes it the quietest of
the last three upgrades. All 202 are aromaticity fixes in macrocycles. Separately, for a few molecules with conjugated
stereo double bonds the canonical SMILES depends on atom order. 21 ChEMBL molecules already had this in 2025.09; 2026.03
added 17 more, and 2026.09 did not fix it.**

| upgrade | canonical SMILES changed | share of ChEMBL 37 |
|---|---:|---:|
| 2025.03.6 → 2025.09.6 | 717 | 0.025% |
| 2025.09.6 → 2026.03.6 | 3,454 | 0.119% |
| 2026.03.6 → 2026.09.1 | 202 | 0.007% |

## What changed in 2026.09

- **The 202 SMILES changes are all aromaticity gains.** Five-membered heteroaromatic rings inside a macrocycle (most
  often furans; also thiophenes, oxazoles or isoxazoles, oxadiazoles, thiadiazoles and thiazoles) stayed Kekulé in
  2026.03.6 and are aromatic in 2026.09.1.
  The 2026.09.1 release notes list the fix as "Aromaticity perception in polycyclic conjugated system"
  ([RDKit issue 9398](https://github.com/rdkit/rdkit/issues/9398)). For 6 of these molecules, the 2026.03.6 output
  was not stable on re-reading; 2026.09.1 fixes all 6. If your set has macrocycles with such rings, recompute their
  keys. No other canonical SMILES changed.
- **Ring counts went up for 1,252 molecules (0.043%), and never went down.** This is the new default ring-finding
  algorithm. The biggest jump we saw was 36 → 586 rings, for two macrocycles (CHEMBL5266504 and CHEMBL5315666);
  the affected molecules include cyclodextrins and cyclophanes. Anything built on `RingInfo.NumRings` or `GetSymmSSSR` changes for these molecules.
- **`RDK_USE_LEGACY_RING_FINDING=1` does not bring the old keys back.** It restores 0 of the 202 SMILES changes and 976
  of the 1,252 ring-count changes. The release notes say: "In a limited number of cases (large macrocycles containing
  multiple para-substituted rings) the new algorithm can take a long time to find the very large number of symmetric
  rings; the old algorithm was faster in these cases, but returned incorrect results." Over all of ChEMBL our pass took
  45% longer with it (per-molecule time summed: 2,613.5 s against 1,798.1 s).
- **InChIKeys did not change** for any of the 99,999 sampled molecules, across all four releases.

## The atom-order regression that 2026.09 did not fix

A canonical SMILES should not depend on how the atoms are numbered. For CHEMBL1290711, 2025.03.6 and 2025.09.6 give one
string for 500 random atom orders. 2026.03.6 and 2026.09.1 give two, 337 and 163 times; the first one is not even stable
when you canonicalize it again. Both have the same InChIKey.

The problem itself is older. Across the 306,699 ChEMBL molecules with double-bond stereo, 21 already gave more than one
string in 2025.09.6 and still do in 2026.09.1. All 21 are axially substituted silicon phthalocyanines or
naphthalocyanines; two of them are paclitaxel conjugates. In 2026.09.1, 17 more molecules give more than one string and
one gets worse (2 → 3 strings), 39 in all. Of those 18, 6 are a coumarin enaminone series, 10 are porphyrin-, chlorin-
or phthalocyanine-like macrocycles, and 2 are neither (a naphthoquinone diimine and a quinolinedione dioxime). That is
rare, but for those series a key-based deduplication silently keeps duplicates.

In our check, canonicalizing twice removed it: `Chem.CanonSmiles(Chem.MolToSmiles(m))` gave one string for all 39
molecules over 100 atom orders in 2025.09.6, 2026.03.6 and 2026.09.1. That is 39 molecules, not a proof; it costs one
extra parse per molecule.

## Check your own set

```python
# keys.py: one "<name>\t<canonical SMILES>" line per input line "<SMILES> <name>"
import sys
from rdkit import Chem

for line in sys.stdin:
    smi, name = line.split()[:2]
    m = Chem.MolFromSmiles(smi)
    print(name, Chem.MolToSmiles(m) if m else "PARSE_FAIL", sep="\t")
```

```sh
uv run --python 3.12 --no-project --with rdkit==2026.3.6 python keys.py < mols.smi > old.tsv
uv run --python 3.12 --no-project --with rdkit==2026.9.1 python keys.py < mols.smi > new.tsv
diff old.tsv new.tsv
```

`checks/keys-uv/` has a five-molecule `mols.smi` and the two outputs; the diff shows the two macrocycles and nothing
else.

## What we ran and what we did not

- **Releases:** 2025.03.6, 2025.09.6, 2026.03.6 and 2026.09.1, PyPI wheels for Linux x86_64 on CPython 3.12, default
  settings, one container per release with no network.
- **Input:** ChEMBL 37, 2,897,819 structures; 15–17 did not parse in each release.
- **Not tested:** conda-forge builds, other platforms, the new nanobind wrappers, descriptor vectors (that run did not
  finish in its time limit), non-ChEMBL inputs. ChEMBL SMILES are already close to canonical, so raw vendor files may
  change more.
- **Lower bounds:** the atom-order scan used 10 orders per molecule (100 for the 39), so it can miss molecules. We
  looked for it after seeing the first results; it was not in our plan.
- **Rerun:** we ran the whole scan a second time from a clean folder, with a fresh ChEMBL download and new
  environments. All 15,762,493 output rows (timing fields left out of the comparison), the counts above and the list of
  18 came out identical; the rerun also found the same 21 older cases. The same team ran both on the same machine, so this is a rerun, not an independent
  replication.

## Files

- `keys.py`: the script above. `atom_order_repro.py`: the CHEMBL1290711 check.
- `results/scored.json`: every count above. `results/iso_changes_V3_V4.json`: the 202 molecules with their 2026.03.6
  and 2026.09.1 SMILES. `results/ringcount_changes_V3_V4.json`: the 1,252 ring-count changes.
  `results/P1_sets.json`: the 18 molecules with their 2026.09.1 strings and whether each is stable on re-reading.
  `results/P1_both.json`: the 21 molecules with more than one string in both 2025.09.6 and 2026.09.1, with their strings
  from each (`p1_sets.py` writes both files).
  `results/renum_chembl_input.json`: 505 atom orders for CHEMBL1290711 and CHEMBL1289158. V1–V4 are the four releases
  in date order; V4L is 2026.09.1 with `RDK_USE_LEGACY_RING_FINDING=1`.
- `scan/`: the scan as we ran it (`worker.py`, `drive.py`, `controls.py`, `score.py`, `dbscan.py`, `renum_repro.py`),
  the input builder, `p1_sets.py`, `canon_twice.py`, the four `pip freeze` files and `run.sh`. `run.sh` and
  `p1_sets.py` were written for this note; the other scan scripts are as run, with only their header lines edited.
- `checks/`: outputs of `atom_order_repro.py` and `canon_twice.py` on each release (`p1_inputs.tsv` holds the 18,
  `p1_both_inputs.tsv` the 21), and the `keys.py` example.

The raw per-molecule output (15.8 million rows) is not included; `scan/run.sh` should regenerate it (see below).

## Rerun it

The small checks need [uv](https://docs.astral.sh/uv/) and network access to PyPI. From this folder:

```sh
uv run --python 3.12 --no-project --with rdkit==2026.9.1 python atom_order_repro.py
uv run --python 3.12 --no-project --with rdkit==2026.9.1 python scan/canon_twice.py checks/p1_inputs.tsv
uv run --python 3.12 --no-project --with rdkit==2026.9.1 python scan/canon_twice.py checks/p1_both_inputs.tsv
```

Compare the output with `checks/repro-and-canon-twice.txt` and `checks/canon-twice-21.txt`. With `rdkit==2025.9.6`
(also on Python 3.12; on Linux it has no wheel for Python 3.15), `atom_order_repro.py` gives one string.

The full scan needs Docker, about 5 GB of disk and about 1.5 hours on 6 CPUs, and scoring needs about 15 GB of RAM.
**We have not run `scan/run.sh` end to end.** It runs the same container commands as our scan, but the script itself is
new. It stops at the first failed step, and `p1_sets.py` refuses output with missing, duplicate or failed molecules.
Use a new, empty work folder; the script writes everything inside it:

```sh
W=$(mktemp -d)
bash scan/run.sh "$W"
cmp "$W/P1_sets.json" results/P1_sets.json
cmp "$W/P1_both.json" results/P1_both.json
```

`$W/scored.json` should match `results/scored.json` except the timing fields (`ms_*`).

The structures in `results/`, `checks/`, `atom_order_repro.py` and `scan/renum_repro.py` are taken from
[ChEMBL 37](https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/chembl_37/) by EMBL-EBI. They and the canonical
SMILES we computed from them are distributed under
[CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/legalcode).

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai.
