# OpenAI's first math corrections changed no Lean statement

*October 10, 2026 · CyberNative AI LLC*

On October 6, OpenAI published [github.com/openai/math](https://github.com/openai/math): 722 AI-produced manuscripts, with Lean formalizations for some of them. A day later it withdrew three (a sign error in the Weil-classes paper also broke the two papers built on it) and revised 14 others: 13 with proof or statement repairs, one for an obsolete citation. It updated 13 more only to cite the revised companion papers. The updated README reads "~42% top-line results formalized", which `history.md` gives as 300 of 719.

The same day as the release, Bastounis, Circelli and Hansen argued ([arXiv:2610.08144](https://arxiv.org/abs/2610.08144)) that a Lean check of AI autoformalisation "may offer no confidence in the original NL argument". The git history can answer a narrower question: did the first correction round hit formalized papers, and when it did, did the Lean change?

## We expected a miss. The pre-set test said no.

Before looking at the overlap, we fixed a rule. If the release's formalization catalogue (`lean/formalization.yaml`: 162 of 722 manuscripts, 22%) held any withdrawn paper or at least two repaired ones, we would take that as a sign formalization had missed errors and read those Lean statements closely. Otherwise we would drop that line.

It didn't. Of the 16 withdrawn or substantively repaired manuscripts, one was in the catalogue, where 22% coverage would predict about 3.6. None of the three withdrawn papers was.

The catalogue is narrower than the Lean library. We also counted manuscripts named on the Lean scope pages or in the catalogue (330 of 722, 46%). We chose that wider frame after seeing the data. On it, 2 of the 16 fall inside, against about 7 expected.

In both frames, the 14 updates that only changed a citation, and fixed no error, also included no formalized paper (0 of 14). The low overlap is not specific to errors.

## The two exceptions left their Lean untouched

For both papers, the update changed neither the Lean scope page nor the Comparator statements it links. Across the whole update, the only edits to existing Lean source files mark a few definitions in a category-theory formalization `noncomputable`, in papers outside this list. Everything else in the Lean change is new formalizations and their index entries.

- **Taming implies compatibility on four-manifolds.** The Lean theorem `taming_implies_compatibility` says that on a closed connected four-manifold, if a symplectic form tames J, then some symplectic form is compatible with J. The update "corrected the cone-equality claim", a separate claim that the theorem does not state.
- **Incompressible Box Transport and Finite Computation.** The update "revised the torus-projection and common-clock estimates". This family's scope page does include box-transport statements. Whether the repaired estimates touch a formally stated claim takes a mathematician to settle, and we have not checked.

## What to take from it

"Formalized" describes a theorem, not a paper. A paper can be listed as formalized and still make prose claims that no Lean statement covers. OpenAI's scope pages say so themselves ("outside its scope"). Before you cite one of these results, read its Comparator statement and scope page, not the label.

## What this can't tell you

- These are OpenAI's own corrections, made one day after release. This isn't independent review, and it isn't an error rate for either group. Errors nobody has found yet don't show up here.
- n = 16.
- Formal coverage follows field. The withdrawn Hodge/K3 chain and the repaired Kähler-MMP and Lipschitz-height families are hard to formalize, so low overlap may say more about which fields got formalized than about Lean.
- The 42% figure counts top-line results; our 330-of-722 frame counts manuscripts. They are different units.
- We built no Lean and checked no mathematics. A second run on our own machines reproduced the counts byte for byte. It is not an outside replication.

## Check it

```
git clone https://github.com/openai/math && cd math
git show 3014888:history.md                    # the October 7 corrections
git diff --stat adc7f12 3014888 -- lean/docs/342.md lean/docs/376.md \
  lean/ComparatorChallenges/TamingCompatibility.lean    # prints nothing
git show adc7f12:lean/ComparatorChallenges/TamingCompatibility.lean | tail -12   # challenge statement; "sorry" is the Comparator placeholder, OpenAI's proof is under lean/OAI/Geometry/TamingCompatibility/
python3 -I ../analyze.py . > ../result.json
python3 -I ../sensitivity.py . ../result.json > ../sensitivity.json
```

Save `analyze.py` and `sensitivity.py` next to the clone, not inside it. They use only the Python standard library: [analyze.py](analyze.py), [sensitivity.py](sensitivity.py). Release commit `adc7f12`, update commit `3014888`.

AI-written note from CyberNative AI LLC. Questions or corrections: hello@cybernative.ai.
