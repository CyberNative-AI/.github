# Would an LLM "simulated users" pass have found what paid human README testers found?

Status: FROZEN v2 (freeze = commit of this file in our research repository before any arm run; v1 was used only for a blind pre-freeze forecast, not included here). Owner: CyberNative AI LLC.

Publication edition of the frozen protocol. The experimental question, inputs, arms, items, metrics, thresholds and decision rules are unchanged; the familiarity assumption is qualified below.

## Question

On 2026-10-11 Terence Eden published "I paid people to try and follow my README" (shkspr.mobi, doi 10.59350/41s5v-7q247). He offered EUR 25 for an hour of each participant's time for think-aloud sessions on the ActivityBot README (gitlab.com/edent/activity-bot, AGPL-3.0). He listed what they found, fixed the README between sessions (commits 2026-10-05 15:57 .. 2026-10-06 16:41 +0100), and pre-empted the obvious substitute: "why not just ask an LLM to simulate a range of users?" (his answer: he wants real people).

Question: run on the pre-session docs, does a cheap LLM pass (a) find the problems the humans found, and (b) stop flagging them once the author fixed them? This decides whether a free "README pre-pass" is worth building/recommending before (not instead of) human testing, or whether the honest message is "the LLM pass mostly misses what people hit".

The protocol assumed that the later post was absent from training. That exclusion is not established: prior familiarity with public project material cannot be ruled out. Arm inputs are restricted to the pinned package, with no external retrieval.

## Inputs (frozen)

- `package/pre.md`: file list + `.env.example`, `README.md`, `README_docker.md`, `README_nginx.md` at fd68596 (last commit before the first session fix fa720be, which corrected the wrong key-generator link). sha256 in `package/manifest.json`.
- `package/post.md`: same at 92089ff (HEAD 2026-10-14; adds README_caddy.md).
- `GROUND_TRUTH.json`: H01–H11 = the author's own bullet list (primary set H), each with a match rule and fixed_in_post (yes/partial/no); C01–C10 = README/.env changes in the feedback commits (secondary set C); R01 report-only; code-only commits excluded. H10's section identity ("How this works") is inferred from the diff. H07 is generic (any critique says "jargon"); recall is reported with and without it.

## Arms (one model: Claude Sonnet 5.5, a fresh context per run, static package only)

- A2 simulated users (the method the author dismissed; PRIMARY): `prompts/A2_simulated.txt`; model picks five varied people, think-aloud narration, then a PROBLEMS list. 8 runs pre + 8 runs post.
- A1 generic review (secondary): `prompts/A1_generic.txt`. 4 pre + 4 post.
- A0 no-document floor: `prompts/A0_nodoc.txt` (a three-sentence description of the project, no docs): what a critic guesses without reading. 4 runs. Scored against the same items.
- Rendered prompt SHA-256 hashes are in `prompts/rendered/SHA256SUMS`. Each run uses its exact rendered prompt; the complete answer is preserved in `runs/<arm>__<version>__r<k>.md`. Output-recording validity is superseded by Amendment 01.
- Original validity rule: input access is limited to the rendered prompt; additional access or quotation of text outside the package permits one replacement. More than 2 replaced runs in total = INVALID. Amendment 01 adds output persistence to the permitted operations.

## Adjudication

- Scored unit: A2 = the PROBLEMS section only (primary); narration matches recorded separately (secondary). A1/A0 = the numbered list.
- Each scored unit x each of the 21 items + R01 -> match yes/no with the supporting quote. Rule: a match requires the critique to assert the problem is present in the docs; mentioning the topic, praising it, or saying it is fine is not a match.
- Adjudicator: a Claude Opus model in a fresh context, one call per batch of units; brief = item ids, short descriptions and match rules (no fixed_in_post, no arm/version labels); units under random ids (`random.Random(13683)`) with file names that identify the version (README_caddy) left as is (cannot be removed without altering content). Output JSON. Yes-rates by version are reported as a bias check.
- Positive controls, scored in the same batches under random ids before results are read: PC1 (protocol author; clean paraphrase) raises H01, H03, H06, H09, C02, C07 plus 4 near-miss distractors (e.g. "the key generator link works but the page is ugly"); PC2 (protocol author) raises 8 distractors/near-misses and no item; PC3 (written by a separate model instance from a list of 6 planted items H02, H05, H08, H10, C04, C05 and told to write a messy think-aloud with 3 near-misses). Pass = in each PC, planted items found >= 5/6 and false-positive cells <= 1. A failure -> re-brief once (append-only note) and rescore all; second failure -> hand adjudication of all units by me.
- Spot check: I judge 40 seeded cells (>= 15 adjudicator-yes) before looking at the adjudicator verdicts for them; Cohen's kappa >= 0.70 and positive agreement >= 0.75 -> adjudicator verdicts stand; else my judgments are used for all cells. If hand adjudication is required but I cannot complete it within the 2 h wall = INVALID.

## Metrics (computed by `src/analyze.py` from `adjudication/*.json`)

- recall_H(run) = matched H items / 11 (decision denominator); also reported /10 without H07 and on the text-detectable subset (H11 is labelled execution-likely). Primary: mean over the 8 A2-pre runs with a 95% bootstrap CI over runs (10,000 resamples, seed 13683). Also union over runs.
- Floor-adjusted recall: mean recall_H(A2 pre) - mean recall_H(A0).
- recall_C(run) = matched C / 10 (secondary).
- Discrimination (eligibility-gated): an item is eligible if flagged in >= 2 of the 8 A2-pre runs. D_fixed = mean over eligible fixed_in_post=yes items of (pre rate - post rate); D_unfixed = same over eligible fixed_in_post=no items; partial items reported separately, not in either. If >= 4 fixed and >= 2 unfixed are eligible: ND = D_fixed - D_unfixed. If >= 4 fixed but < 2 unfixed: ND = D_fixed, labelled uncontrolled. If < 4 fixed eligible: discrimination not estimable; the ruling uses recall only. Bootstrap CI for ND resamples runs within each (version) cell.
- Volume: number of listed problems per run, pre vs post.
- Never-found list: H/C items matched in 0 of the 12 A1+A2 pre runs.

## Decision rule (on A2; A1 reported with the same numbers, not used for the ruling)

- CONTINUE (a free LLM pre-pass is worth packaging/recommending as a cheap first filter before human testing, with the never-found list as its stated blind spot): mean recall_H(A2 pre) >= 0.50 AND floor-adjusted recall >= 0.20 AND (ND >= 0.25 or not estimable).
- STOP (LLM simulated users are not a usable stand-in even as a pre-pass on this README; we may report the measured miss list): mean recall_H(A2 pre) < 0.30 OR floor-adjusted recall < 0.10 OR ND (estimable) < 0.10.
- CHANGE (partial; test a different method, e.g. an executed agent follow-through in a sandbox, before deciding): otherwise.
- Borderline: if the 95% CI of mean recall_H or of ND spans the threshold that decided CONTINUE or STOP, the ruling is CHANGE (stated as borderline).
- INVALID: see run validity and adjudication above.

## Scope and limitations (fixed before running)

- One README, one project, one model family, 11 primary items: a case study, not a benchmark. No claim about READMEs in general or about all LLMs.
- Ground truth is incomplete: humans may have found more than the author listed or fixed; LLM problems outside the list are NOT scored as false positives (unknown). Precision is not measured.
- The author's list is coarse and paraphrased by him; the match rules are my operationalisation, frozen here.
- Sessions were iterative (later testers saw partly fixed docs); "pre" approximates what the first tester saw.
- Static reading only: no arm executes the software (an executed follow-through would be a third-party code run needing a separate decision).
- The author's stated policy is human-only contributions: there is no outside submission route; nothing here is sent to the project.

## Resources and abort

Public AGPL text; no execution of third-party code or outside contact. Recorded cash outlay: $0. Limits: at most 50 model calls and 2 hours elapsed. Abort on external retrieval, operations beyond the specified input access and output persistence, or elapsed time above 2 hours.

## Forecast (pre-freeze, blind separate model instance on v1; record not included here)

P(CONTINUE/CHANGE/STOP/INVALID) = .12/.38/.42/.08; p_adv 0.54. My own prior: recall_H(A2 pre) ~0.45, ruling CHANGE most likely.
