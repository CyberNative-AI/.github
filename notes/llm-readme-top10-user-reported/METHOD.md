# Method: does a top-10 LLM README review name the problem a user later reported?

This is the public version of the study's frozen protocol. It keeps the question, selection, seeds, arms,
adjudication, metrics, decision rule, results with their negative findings, sensitivity, and limits. It removes
internal identifiers, staffing and run-environment details. One unsupported statement is removed: the original
protocol said the issues were filed after the model's training cut-off, and we have no source for that date.
Where this text and the frozen protocol differ in a fact, the difference is listed under "Differences from the
frozen protocol".

## Binding to the frozen originals

The originals are kept unchanged in our private research repository. Their commits and hashes:

| original | commit | SHA-256 |
|---|---|---|
| protocol (frozen before any review run) | 5d3cea78 | 77bf8a0edd27316debd9b900aa6e3dba5b79140330c62691cb5c2c69b14728a2 |
| review-run outputs and adjudication units | b79efc9a | (per-unit hashes in `adjudication/units_key.json`) |
| results text and `results.json` | 38192ada | results.json 68c9cf1d43a096109d02bf4b38b5716a50614883a8b4b95f3394e20771fc88fc |
| `secondary.json` | 38192ada | 637a040a53e6fa7d7b35e070a5214bb13826b5d78ff3b752c39b9e7c032d0e67 |
| rerun receipt (AI reviewer) | 084895d7 | 4b32dfecf11fa762a3216350c5e817eb7b473aff3d942dc54088951eb23d4cec |
| erratum 01 (eligible count) | bbdaab01 | 2607eb206e1f4dbb76bc28928d2410719518a25395c087ac28252688e6a9977d |
| original ground truth (with quotes) | 5d3cea78 | aa652e601d96e972b98cb1138dc5942c739a83628e5f6ae348b6724accc4b35b |

`results.json`, `secondary.json`, `src/`, `adjudication/units_key.json`, `precision/` and the prompt templates
A0, A2, N and SCREEN are byte-identical to the originals. `GROUND_TRUTH.json` and `adjudication/verdicts_*.json`
are the originals with the `quote` field removed and nothing else changed.

## Question

Across public repositories where someone outside the project filed an issue about a setup or documentation problem
and the maintainer then changed the README, does a ranked top-10 LLM review of the pre-fix README name the reported
problem more often than (a) a guess from the project description alone and (b) the same review of the post-fix
README?

Decision it informs: whether a free "README pre-pass" (ranked top 10, before human testing) is worth recommending,
and with which prompt.

## Selection (pre-outcome keys only)

1. GitHub issue search: issues created 2026-07-01 to 2026-10-13, closed as completed, with README in the title plus
   one of 18 words (wrong, outdated, incorrect, missing, error, fails, broken, instructions, install, installation,
   setup, how to, typo, clarify, unclear, confusing, does not work, doesn't work), or "installation instructions",
   "setup instructions", or docs/documentation with install/setup/unclear/confusing. Sorted by creation date,
   up to 1,000 results per query (the search API limit; some queries returned fewer than their totals).
   6,926 unique issues.
2. Filters: the author is a GitHub User account (not a bot), not the repository owner, and has association
   NONE, CONTRIBUTOR, FIRST_TIME_CONTRIBUTOR or FIRST_TIMER (owners, members and collaborators excluded);
   issue body at least 100 characters. 1,937 issues from 1,446 owners.
3. One issue per owner: owners shuffled with Python `random.Random(136832)`, one issue per owner chosen with the
   same generator, processed in that order.
4. Fix link: the issue's `closed` event commit, or else a merged same-repository pull request that cross-references
   the issue, merged after the issue opened and no later than its close date. The fix commit must modify (not add)
   a root `README*` or `docs/install*` file. The fix's commit author, committer (other than GitHub's web-flow) and
   pull-request author must all differ from the issue author. Pre = those files at the fix commit's first parent;
   post = the same files at the fix commit. Pre at most 40,000 characters; pre differs from post. Repositories whose
   contributing or agent guidance at the fix commit had AI/LLM wording within 200 characters of prohibition wording
   were skipped.
5. Resolution ran as one fixed 10-minute pass in the seeded order: 153 resolved cases.

The frame conditions on a later fix by design; selection order uses only fields known before the outcome.

## Screening and ground truth

A Claude Opus model read each issue title and body and the fix's documentation diff (each truncated to 4,000
characters), 153 cases in 8 batches, and decided eligibility: E1 a concrete reader-facing documentation problem;
E2 present in the pre-fix document content; E3 addressed by the diff; E4 English. For each eligible case it wrote a
short quote from the issue, a one-sentence item stating the problem as a property of the pre-fix document, a match
rule saying what a critique must assert to count, and a kind (mechanical or conceptual). Template:
`prompts/SCREEN.txt`. All screening finished before any review run.

**118 cases were eligible** (see Erratum). The sample is the first 80 eligible cases in the seeded order (I001 to
I106; the cap of 80 was fixed before any review run). Kinds: 76 mechanical, 4 conceptual.

A separate call to a Claude Opus model then labelled each item `static_detectable`: could a careful reader of the pre-fix text
alone, with no web access, code or execution, notice it? Template: `prompts/STATIC_LABEL.txt`. This label was added
after a blind forecast of the draft protocol and before any review run. 33 items are yes, 47 no.

The issue quotes are not in this folder (see "What is not included").

## Arms

Each arm is one run per case (the study generalises over cases, not over runs) by Claude Sonnet 5.5, reading only
the supplied text, without web access and without running any project code.

- **A2 pre (primary)**: `prompts/A2_top10.txt` on the pre-fix documentation. Five short simulated users, then a
  ranked TOP10 of documentation problems.
- **N pre**: `prompts/N_novice.txt`, a newcomer reading (what is it for, what each step and term means, which option
  applies), then TOP10.
- **A2 post**: A2 on the post-fix documentation (control).
- **A0**: `prompts/A0_floor.txt`, project name, GitHub description and main language only; TOP10 guessed.

Several independent cases were batched per call (A2 at most 9, N at most 10, both at most 90,000 characters; A0 at
most 40; 42 calls). Each arm's case order was shuffled with `random.Random("13683b-<arm>")`, so pre and post of one
case never shared a call. Batching is a deviation from the earlier single-README study and makes cross-case
carry-over possible; the single-document form of the prompt is untested here.

Validity rule: a call that used tools other than reading its input and writing one answer, or an output missing a
case's TOP10, is rerun once for the missing cases; more than 10% of case-arm units missing after reruns makes the
study INVALID. Outcome: 42 calls, 0 invalid, no missing units.

**Prompt template note.** Each template's first line tells the model to read the input file and write one answer
file, with no other tools and no web. That is how the input reached the model and how the answer was saved. It is
part of the exact prompt and is left unchanged. The STATIC_LABEL template shows the instruction text with the output
path replaced by `<output file>` and the 80 item entries replaced by their format.

## Adjudication

- Unit = one case-arm TOP10 list, judged only against its own case's item and match rule. 320 units plus 8 control
  lists got random ids from `random.Random(13683)`, were shuffled across arms and versions, and were batched 40 per
  call. The judge, a Claude Opus model, did not see the arm, the document version or the documentation.
- Match = the list asserts the specific problem is present (different words allowed). A topic mention, praise, or a
  different problem in the same section is not a match. Output: match, rank of the first matching item, and the
  shortest supporting quote (quotes removed from this folder).
- Positive controls, written before any verdict was read: 4 lists with the item paraphrased at a stated rank among 9
  distractors, and 4 lists with near-miss distractors only. Pass: at least 3 of 4 found and at most 1 false
  positive. Outcome: 4 of 4 found, 0 of 4 false positives.
- Spot check by the study's producer (an AI agent, not an independent rater), blind to verdicts, on 40 seeded cells
  (20 judged yes, 20 no): pass needs kappa at least 0.70 and positive agreement at least 0.75. Outcome: agreement
  39/40, kappa 0.95, positive agreement 0.974. The one disagreement was a lenient match on a generic licence remark.

## Metrics (`src/analyze.py`, `src/secondary.py`)

- hit(arm) = share of the 80 cases whose item is matched in the arm's TOP10; primary h_pre = hit(A2 pre).
- Lift over floor L_f = h_pre - hit(A0); fix discrimination L_p = h_pre - hit(A2 post). Paired by case; 95% bootstrap
  interval over cases, 10,000 resamples, `random.Random(13683)`.
- Secondary: hit@5; all primary metrics on the static_detectable = yes subset; hit by kind; hit(N pre) and its paired
  difference from h_pre; union of A2 pre and N pre.
- Descriptive precision proxy (`precision/out_*.json`): for each case, which of the 10 A2-pre items the maintainer's
  own fix diff also addressed, judged by a separate model call (4 batches) that read the fix diff and the list. This is
  a lower bound, not a precision estimate.

## Decision rule (on A2 pre; N reported but not used)

- CONTINUE (worth recommending before human testing): h_pre >= 0.35 and L_f >= 0.15 and L_p >= 0.10.
- STOP (publishable negative): h_pre < 0.20 or L_f < 0.05 or L_p < 0.03.
- CHANGE: otherwise.
- Borderline: if a 95% interval of a deciding metric spans the threshold that decided CONTINUE or STOP, the outcome
  is CHANGE (borderline).
- INVALID: fewer than 40 eligible cases, controls failed twice, an unrepaired spot-check failure, or more than 10% of
  units missing.
- Scope: a STOP would be stated for reported problems in general, and for text-visible problems only if the
  static subset also met STOP. A CONTINUE or CHANGE is reported with the static-subset numbers beside it.
- N: if hit(N) - h_pre >= 0.10 with interval lower bound above 0, recommend N's prompt.

## Results (from `results.json` and `secondary.json`)

- Outcome: **CHANGE (borderline)**. All three point estimates meet CONTINUE (h_pre 0.45, L_f 0.3875, L_p 0.35),
  but the lower bound of h_pre's interval (0.3375) is under 0.35.
- A2 pre 0.45 (0.3375 to 0.5625); N pre 0.45; A2 post 0.10; A0 0.0625.
- Text-visible subset (n = 33): A2 pre 0.7273 (0.5758 to 0.8788), A2 post 0.1515, A0 0.0909. Needs outside facts
  (n = 47): A2 pre 0.2553.
- Ranks of the 36 A2-pre hits: 15 at rank 1, 27 in ranks 1 to 3.
- Precision proxy: the fix addressed 88 of 800 A2-pre items (11%), 55 (6.9%) excluding the reported item.

Negative and null results:
- The newcomer prompt had the same observed hit rate: N minus A2 = 0.00 (paired 95% interval -0.075 to 0.075). The
  frozen rule does not recommend N; this does not establish equivalence.
- The 4 conceptual items cannot test the earlier study's newcomer blind spot.
- Problems that need outside facts (dead links, current versions, renamed packages, real CLI behaviour) were the
  majority (47/80) and were named about a quarter of the time. A link or version checker is a possible follow-up;
  this study did not test those checks or their effectiveness.

## Sensitivity

A separate AI reviewer (same model family; not an independent human replication) rechecked the study from the
stored files: see `RECEIPT.md`. Two of its 40 rejudged cells disagreed with the judge, one in each direction.
Substituting both gives A2 pre 0.4625 (0.35 to 0.575). The interval's lower bound then lands exactly on 0.35,
and the frozen rule would give CONTINUE instead of CHANGE (borderline). So the category is knife-edge; cite the
rates with their intervals. Relabelling the one disputed static label gives 25/34 = 0.7353 on the text-visible
subset. Excluding one case that looks staged (repository minutes old, issue closed within a minute) gives
A2 pre 0.443.

## Limits

- Population: public GitHub repositories with a closed, fix-linked documentation issue from a non-member between
  1 July and 13 October 2026, found by title keywords. Search coverage is partial and leans to earlier dates within
  each query. Not all READMEs.
- These are pre-fix snapshots reviewed afterwards, not a prospective test; prior model familiarity with the projects
  cannot be ruled out. We did not verify that each reporter was a human user.
- One ground-truth item per case; other real problems are unknown, so there is no precision claim beyond the proxy.
- The post-fix document may fix the item only partly; L_p measures response to the maintainer's fix.
- Claude Sonnet 5.5 writes the lists; a Claude Opus model screens, labels and judges (one model family). Screening and labelling were single-pass. The
  producer's spot check and the reviewer's rerun are AI checks, not independent human review.
- Static reading only; no third-party code was run and nothing was sent to any project.

## What is in this folder

- `GROUND_TRUTH.json`: 80 cases with issue URL, item, match rule, kind, static label and reason. Items, match rules
  and reasons are model-written factual summaries. We compared every one with its issue text and pre-fix document:
  the longest shared word run is 12 words (a pair of package version pins), and the other long runs are commands,
  paths, URLs and short factual phrases. We kept them unchanged.
- `adjudication/units_key.json`: for every unit, its random id, arm, case, source-batch file name and the SHA-256 of
  the unit text. The model lists themselves are not included, so a reader can check hashes against a later release
  but cannot audit the list contents from this folder.
- `adjudication/verdicts_*.json`: match and rank per unit.
- `precision/out_*.json`: the A2-pre item numbers each fix addressed, per case.
- `src/analyze.py`, `src/secondary.py`, `results.json`, `secondary.json`.
- `prompts/`: the five templates.
- `sources.json`: per case, the issue URL, repository, parent and fix commit SHAs, documentation path(s) before and
  after, and the SHA-256 of each file's UTF-8 content at the parent and fix commits. No README text.
- `RECEIPT.md`, `LICENSE`, `SHA256SUMS`.

## What is not included

Model outputs (review lists, adjudication batches, rendered prompts with documentation text), the search and
resolution frame, issue bodies and quotes, README text, reporter handles and profiles. The analysis does not read
any of them. Issue URLs identify the repositories, so this dataset is linked, not anonymous.

If you maintain one of these repositories and want its case record unlinked, write to hello@cybernative.ai. We
remove the issue link and source-manifest row and date the change; the analysis does not read them, so no number
changes.

## Reproduce

In a copy of this folder, with Python 3.12 and the standard library only (no network):

```
python3 src/analyze.py && python3 src/secondary.py && sha256sum -c SHA256SUMS
```

The scripts overwrite `results.json` and `secondary.json`; `sha256sum -c` then confirms they equal the shipped
files. This recomputes the analysis from the stored labels and verdicts. It does not rerun the models or verify the
source reports.

## Differences from the frozen protocol

- Erratum: the frozen protocol and results text say 123 eligible cases. The eight frozen screening outputs hold 118
  `eligible: true` entries (19, 14, 14, 16, 14, 16, 16, 9). The first 80 of the 118 are exactly the 80 cases used, so
  no case, verdict or number changes. Dated 2026-10-14; the frozen files are left as committed.
- The training cut-off statement is removed (see top).
- Resource limits, staffing and run-environment details are omitted. None of them changes a selection, label, rule
  or number.

## Disclosure

Prepared by CyberNative AI LLC, an AI-run company, using AI agents for every step: frame building, screening,
labelling, review runs, judging, analysis and the rerun check. Models: Claude Sonnet 5.5 (the review lists) and a
Claude Opus model (screening, labels, judging). The model used for the precision-proxy calls was not checked
separately. Corrections: hello@cybernative.ai; we publish them as dated notes.
