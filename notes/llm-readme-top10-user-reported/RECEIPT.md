# Rerun receipt

A separate AI reviewer (same model family as the study; not an independent human replication) rechecked the study
from its stored files on 2026-10-14. No review-model or judge run was repeated. Cost: none beyond the reviewer's
own run. This is the public version of the reviewer's receipt (original SHA-256
4b32dfecf11fa762a3216350c5e817eb7b473aff3d942dc54088951eb23d4cec, see METHOD.md). Case ids (I…) and unit ids (U…)
refer to `GROUND_TRUTH.json` and `adjudication/units_key.json`.

**Verdict: reproduced.** The stored inputs and verdicts reproduce every number in `results.json` and
`secondary.json`. The reviewer's own judgments agree closely with the judge, the static labels and the screening.
No headline number changes. The decision-rule category is knife-edge (see Sensitivity), so cite the rates with
their intervals.

## 1. Inputs

Ten cases drawn with `random.Random(20261014).sample(sorted(GROUND_TRUTH), 10)`: I088, I025, I021, I079, I095,
I083, I053, I059, I051, I086. Their documentation files were fetched anonymously from GitHub at the parent and fix
commits listed in `sources.json`.
- 10/10 pre-fix and 10/10 post-fix files byte-identical to the stored text (the hashes in `sources.json` are of that
  stored text).
- 10/10 issues dated on or after 2026-07-01. 10/10 reporters differ from every fix author.
- 10/10 fix commits touch the listed documentation file and have the listed parent. Only 3 of 10 commit messages cite
  the issue number, so the issue-to-fix link rests on the screening criterion E3, not on commit text.
- Across all 80 cases (offline): every issue is dated 2026-07-01 or later; no reporter is a fix author.
- Stored model outputs: 42/42 file hashes match. Regenerating the adjudication units from them gives a units key
  byte-identical to `adjudication/units_key.json` (328 units, 0 missing).
- One case (I002) looks staged: the repository was minutes old with no stars, and the issue was closed within a
  minute of opening. Excluding it moves A2 pre from 0.450 to 0.443. Excluding the four cases whose repositories were
  under 3 days old when the issue was filed (I001, I002, I044, I080) gives 0.447. Not material.

## 2. Analysis scripts

`src/analyze.py` and `src/secondary.py` on a scratch copy produce `results.json` and `secondary.json`
byte-identical to the stored files.

## 3. Rejudging 40 adjudication cells

Sample: 40 non-control units, `random.Random(20261014).sample` over the sorted non-control unit ids. The draw held
15 units the judge had marked as matches. The reviewer judged each from the case's item and match rule and the
unit's list, then compared.
- Agreement 38/40, Cohen's kappa 0.893, positive agreement 0.933 (judge 15 matches, reviewer 15).
- U78246 (A0, I056; licence badge conflicts with the stated licence): judge match, reviewer no match. The list only
  says licence and packaging are unclear and names no conflict. The judge was lenient.
- U95665 (A2 pre, I007; `go install` at the module root): judge no match, reviewer match. The list's first item says
  the root install command does not match the documented tools. The judge was strict.
- Four further borderline matches (U56484, U49388, U20985, U16531) were agreed.

## 4. Labels and screening

- `static_detectable`: 20 seeded items judged from the item and the pre-fix README before reading the stored labels.
  Agreement 19/20. The difference is I059: the pre-fix README names one file in a command and a differently spelled
  file in its own file list, which a reader can see. The stored label was "no". The original labeller saw only the
  item text, not the document, so such cases can be under-called.
- Screening: 15 seeded cases (I140, I045, I039, I124, I152, I131, I085, I092, I082, I135, I091, I112, I080, I114,
  I111) judged under `prompts/SCREEN.txt` before reading the stored screening. Agreement 15/15 (11 eligible, 4 not).

## 5. Sensitivity

Stored: A2 pre 0.45 (0.3375 to 0.5625), A0 0.0625, A2 post 0.10, L_f 0.3875 (lower bound 0.275), L_p 0.35,
text-visible subset (n = 33) 0.7273.

With the reviewer's two disagreements substituted (scratch copy only; stored verdicts unchanged):
- A2 pre 0.4625 (0.35 to 0.575), A0 0.05, L_f 0.4125, L_p 0.3625.
- The frozen rule calls an interval borderline when its lower bound is under 0.35. The lower bound lands exactly on
  0.35, so the category moves from CHANGE (borderline) to CONTINUE.
- Relabelling I059 as text-visible: n = 34, A2 pre 0.7353 (0.5882 to 0.8824); category unchanged.

The two disagreements go in opposite directions in this sample; this does not establish absence of systematic bias.
They show that changing 2 of 328 cells moves the category across the threshold. There are 320 non-control units (328
total minus 8 controls); after rejudging 40, 280 non-control units remain unchecked, so the net direction over all
cells is unknown. The stored outcome stands; this receipt is not a new ruling. Use the rates with their intervals:
about 0.45 overall (roughly 0.34 to 0.56) and about 0.73 on text-visible items.

## Limits

- One AI reviewer, so this is a rerun and second pass, not a human replication; a model reviewer may share blind
  spots with the judge.
- The 40, 20 and 15 samples are small; kappa 0.89 has a wide interval.
- The fetch checks confirm file bytes, dates, authorship and commit contents. They do not recheck that each README
  problem was real beyond the screening rules.

## Folder check (2026-10-14)

On a fresh copy of this folder, Python 3.12.3, standard library, no network:

```
python3 src/analyze.py && python3 src/secondary.py && sha256sum -c SHA256SUMS
```

Both scripts regenerate `results.json` (SHA-256 68c9cf1d43a096109d02bf4b38b5716a50614883a8b4b95f3394e20771fc88fc)
and `secondary.json` (637a040a53e6fa7d7b35e070a5214bb13826b5d78ff3b752c39b9e7c032d0e67), byte-identical to the
original files, and every entry in `SHA256SUMS` checks OK. Removing the `quote` fields changed no result.
