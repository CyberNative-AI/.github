# Results: LLM "simulated users" vs paid human README testers (ActivityBot)

Ruling (frozen rule, `src/analyze.py` → `results.json`): **CHANGE (borderline)**. Point estimates meet CONTINUE; the net-discrimination bootstrap CI lower bound (0.246) falls just under 0.25, and the protocol sends a borderline CI to CHANGE.

Status: `Executed`. `Results reproduced` by a second reviewer from the committed files (same company, same model family; not replicated). See `rerun/RERUN.md`. Protocol and Amendment 01 (output recording) were frozen before the scored arm runs.

## Setup in one paragraph

Ground truth = Terence Eden's own list of what his paid think-aloud testers found ("a few people", €25 for an hour of their time; 11 items, H01–H11; blog post 2026-10-11) plus 10 README/.env fixes in his 2026-10-05/06 "user feedback" commits (C01–C10). Arms ran on the pre-session docs (fd68596) and on the fixed docs (92089ff): A2 "simulate five varied users, then list PROBLEMS" (primary, 8+8 runs), A1 generic review (4+4), A0 a three-sentence description with no docs (4 runs, the floor). One model (Claude Sonnet 5.5, a fresh context per run, static package only; 28 retained runs and one unsuccessful attempt replaced). Blind adjudication by a Claude Opus model of 47 units × 22 items against frozen match rules.

## Validity checks

- Positive controls: PC1 6/6 planted, 0 FP; PC2 0 FP; PC3 (written by a separate model instance, messy) 6/6 planted + all 3 extra true items, 0 FP.
- Blind spot check (40 cells, the researcher vs the adjudicator): agreement 0.90, Cohen's kappa 0.783, positive agreement 0.857 → adjudicator verdicts stand. **Direction:** all 4 disagreements were adjudicator-yes / researcher-no (lenient matches: a path inconsistency in "How this works" counted as H10; a hedging nginx comment counted as a joke for H06; a Quickstart/Set Up contradiction counted as H08 and as H02). Recall figures therefore lean generous to the LLM arms.
- Second spot check (40 cells, `rerun/`): kappa 0.900, positive agreement 0.950. One cell had been seen previously; excluding it gives kappa 0.949 on 39 cells. Across both checks there were four distinct lenient H matches and one strict report-only match; flipping the four H matches moves mean recall_H (A2 pre) from 0.602 to 0.580.
- Mean matched items per unit: pre 11.6, post 9.35, no-doc 5.75.

## Primary numbers (H = author's 11 items)

| arm | runs | mean recall_H | 95% CI | w/o H07 | recall_C | problems listed / run |
|---|---|---|---|---|---|---|
| A2 simulated, pre | 8 | **0.602** | 0.545–0.659 | 0.625 | 0.637 | 30–38 (one 21) |
| A2 simulated, post | 8 | 0.500 | 0.432–0.568 | 0.537 | 0.500 | 34–46 |
| A1 generic, pre | 4 | 0.591 | 0.500–0.682 | 0.625 | 0.400 | 15–23 |
| A1 generic, post | 4 | 0.523 | 0.455–0.591 | 0.550 | 0.350 | 18–22 |
| A0 no docs | 4 | 0.273 | 0.136–0.409 | 0.225 | 0.275 | 12–15 |

Floor-adjusted recall (A2 pre − A0) = 0.329. Union over the 8 A2-pre runs: 10/11 H items.

## Discrimination (A2, eligible = flagged in >= 2 of 8 pre runs)

D_fixed 0.25 over 10 fixed items; D_unfixed −0.167 over H02, H03, H05; ND 0.417, CI 0.246–0.571 (controlled).

Per item, A2 pre → post (of 8):
- Clean drops where the fix is crisp and checkable: H01 wrong key-generator filename 8→0; C01 cURL missing from requirements 8→0; H10 "How this works" section 3→0 (section removed); C06 Apache assumption / hidden other-server docs 7→4.
- Still flagged after the author's fix: C07 HTML elements 7→8 (fix points to a PHP variable, `$allowed_elements`); C08 avatar step 8→8; C09 config route / files to upload 8→7; H04 local vs hosted key tool 4→3; H08 section order 2→6 (the new Quickstart contradicts Set Up, a problem the fix introduced).
- Unfixed controls: H03 hidden dotfiles 8→8, H05 quoting 7→8, H02 "what does rename mean" 2→5.
- Partial: H06 jokes 8→5, H11 permissions 8→8, C04 password hash needs local PHP 7→8, H07 jargon 3→1.

Label sensitivity (found by the second reviewer, not in the protocol): with C07 and C08 relabelled partial, ND is 0.495 (CI 0.318–0.656) and the frozen rule gives CONTINUE. The ruling above uses the labels as frozen.

## What the LLM passes missed

- Never matched in any of the 12 A1+A2 pre runs: C03 (REALNAME "real" name vs display name) and C10 (PAGE_SIZE: per page of what).
- Rare in A2: H09 "I hadn't actually explained what the software would do." 0/8 (A1 2/4); H02 "What does it actually mean to rename a file?" 2/8; H07 jargon 3/8; H10 3/8.
- Pattern: in this test the simulated users missed several basic newcomer questions, although renaming was flagged in 2/8 runs and hidden-file handling in 8/8. The named mechanical defects were each flagged in 7–8 of 8 runs.

## Post hoc (NOT in the frozen protocol; exploratory, `src/posthoc_topk.py` → `posthoc_topk.json`)

Recall_H if a maintainer reads only the first k problems of each list:

| arm | top 5 | top 10 | top 15 | top 20 | all |
|---|---|---|---|---|---|
| A2 pre | 0.193 | 0.386 | 0.500 | 0.557 | 0.602 |
| A1 pre | 0.136 | 0.364 | 0.455 | 0.591 | 0.591 |
| A0 no docs | 0.114 | 0.182 | 0.273 | 0.273 | 0.273 |

The 0.60 headline comes with ~33 listed problems per run. A maintainer reading ten gets ~0.39.

## Interpretation (scoped to this README, this model, this ground truth)

- Observation: on this README, an LLM "simulate a range of users" pass would have surfaced about 60% of the problems the author's paid testers reported, about 33 points above what the same model guesses from a one-paragraph description. The pass also stopped flagging the crisp defects the author fixed.
- Observation: several basic newcomer questions were missed in this test; the omissions were not universal (renaming: 2/8, hidden files: 8/8).
- Inference: these results suggest a static LLM pass can flag some mechanical defects before a human session; its extra suggestions still need triage.
- Not shown: precision (remaining suggestions were not checked for correctness; the ground truth is incomplete); any other README, model or audience; whether real users hit the extra LLM items; executed follow-through (static reading only).

## Limitations

One README, one project, one model family generating and judging (Claude Sonnet 5.5 wrote the lists, a Claude Opus model judged them; lenient direction measured). The author's list is coarse and was turned into match rules by us (frozen before the scored arm runs). Sessions were iterative, so "pre" approximates what the first tester saw. H10's identity was inferred from the diff. Earlier versions of the README are public, and prior familiarity with public project material cannot be ruled out. The tested commit fd68596 (2026-09-30) was substantially revised in August and September (24 commits touching README.md/.env.example); the post and feedback fixes came later.

## CHANGE: what would decide it

A generalisation and precision test, not more runs on this README: (1) a frame of public READMEs where a real user's issue reported a setup-doc problem and the maintainer then fixed the README, each with an issue-anchored ground-truth item. Does a ranked top-10 LLM pass on the pre-fix README flag that item more often than the no-doc floor? (2) a novice-targeted prompt arm aimed at the measured blind spot (H09/H02/C03-type items). Static reading, CPU, no outside contact.

## About this folder

This folder contains the experiment's protocol, amendment, prompts, model outputs, match verdicts, analysis scripts and reproduction evidence. The retained numerical results, prompt text, model outputs and scoring rules are unchanged; editorial corrections qualify familiarity, judging and interpretation. Not included: the rendered prompts and `package/pre.md`/`post.md` (they contain the full ActivityBot docs; `src/build_package.py` and `src/render_prompts.py` rebuild them from the two public commits, checked against `package/manifest.json` and `prompts/rendered/SHA256SUMS`), the clone, and the pre-freeze forecast record. Licences: `LICENSE` and `UPSTREAM-NOTICE.md`.
