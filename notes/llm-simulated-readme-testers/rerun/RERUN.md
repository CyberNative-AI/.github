# Second-reviewer rerun

Verdict: **reproduced.** Inputs, scoring and the ruling reproduce byte for byte. A second blind judgment of 40 cells agrees with the adjudicator (kappa 0.90). One caveat matters and is in section 5: the borderline CHANGE ruling depends on two `fixed_in_post` labels.

Scope: 2026-10-14, CPU, standard-library Python 3 (`python3 -I`), $0. The committed bytes were scored as the protocol requires; no model arm and no adjudicator was re-run. The project and its author were not contacted.

Status words: `Executed` and `Results reproduced` for the deterministic pipeline. The reviewer works for the same company, so this is not `Results replicated`. The reviewer is also an AI model of the same family as the arms and adjudicator, so the judging check is a second-reader audit, not a model-independent one.

## 1. Inputs re-derived

- Fresh clone of gitlab.com/edent/activity-bot (HEAD 92089ff3, no commits after the post-fix version). `src/build_package.py <clone> <out>` produced `pre.md`, `post.md` and `manifest.json` byte-identical to the originals; `package/manifest.json` here is that manifest.
  - pre fd68596: package_sha256 `3d4b873c…74d`, 3264 words.
  - post 92089ff: package_sha256 `b0af09a0…8bc`, 3570 words.
- `prompts/rendered/SHA256SUMS`: 5/5 OK (on the rendered prompts, which are not included in this folder). `runs/SHA256SUMS`: 28/28 OK. Run `sha256sum -c` from the folder root.

## 2. Analysis re-run

On a scratch copy:

- `src/analyze.py` → `results.json`: **byte-identical**.
- `src/posthoc_topk.py` → `posthoc_topk.json`: **byte-identical**.
- No number changed: ruling CHANGE (borderline); recall_H A2-pre 0.602 (CI 0.545–0.659); floor-adjusted 0.329; ND 0.417 (CI 0.246–0.571); post-hoc top-10 recall 0.386.

## 3. Ground-truth review (`GROUND_TRUTH.json` not edited)

Sources: the blog post (its 12 bullets match H01–H11 plus R01, in the author's order) and fd68596..92089ff (18 commits).

Labels the reviewer would keep: H01 (fa720be changes `rsa_keys.html` to `rsa_key_generator.html`; "demo tool" is the key generator), H02, H03, H05 (unfixed: the "rename" wording and the mixed quoting are untouched), H04, H09, C01–C06, C09, C10.

Labels the reviewer would change or flag:

| item | current | suggest | reason |
|---|---|---|---|
| C07 | yes | partial | The fix changes the text to "See `$allowed_elements`". That points into `index.php` and still does not say which elements are allowed, so the problem the match rule describes is still present. 7/8 → 8/8 flags after the "fix" is the symptom. |
| C08 | yes | partial | The new text is "Edit `.env` to include the image locations". It names `.env` but still not the variable names or where to upload the images. 8/8 → 8/8. |
| H10 | yes | keep, mark low confidence | The blog bullet does not name the section. "How this works" was removed in the post-fix docs and fits "technically interesting to me", but the link is inferred from the diff (already flagged `inferred_from_diff`). |
| H11 | partial | keep | The package diff adds permission text only in the new `README_caddy.md`. The `mkdir` 0744→0775 change is code, not docs. It is outside both ND sets, so the label has no effect on ND. |
| H08 | yes | keep, note | The author moved Set Up and added a Quickstart. The Quickstart then contradicts Set Up on rename and upload order, so reviewers flag order *more* (2/8 → 6/8). That is a real regression the fix introduced, and it counts against the LLM pass's "drop" metric. |

## 4. Independent 40-cell judging

- Sampling (`rerun/sample_cells.py`, `random.Random(20261014)`): pool = non-control, non-narration units (27 after excluding U3972, see below) × 22 items. Sampled 20 adjudicator-yes (≥15 required), 12 adjudicator-no cells in an (arm, version) where the same item is matched elsewhere (near-miss), and 8 other no cells. The script printed only counts; the reviewer received an unlabeled, shuffled cell list.
- The reviewer read the unit text in `adjudication/batch_*.md` and judged each cell against `adjudication/BRIEF.md` before opening any verdict for it, and did not open `adjudication/spotcheck_*` until judging was finished.
- Data: `rerun/judged_cells.json` (the reviewer's judgment, the adjudicator's verdict and the stratum for each cell).

Result (40 cells): both yes 19, adjudicator-yes/reviewer-no 1, adjudicator-no/reviewer-yes 1, both no 19.

| statistic | value |
|---|---|
| agreement | 0.95 |
| Cohen's kappa | **0.900** |
| positive agreement | **0.950** |
| reviewer yes / adjudicator yes | 20 / 20 |

Disagreements:
1. U9207 · H10 · adjudicator **yes**, reviewer no. The unit lists inconsistent paths (`/data/...` versus `/posts`, `/quotes`) in the "How this works" section. That is a different problem in the same section, which the brief excludes. The researcher's own spot check flagged the same cell (S00), so two judges call it a lenient match. Direction: adjudicator-lenient.
2. U6404 · R01 · adjudicator **no**, reviewer yes. The unit says the "0./1." numbering "will render oddly in some viewers"; the reviewer read that as a markdown-rendering concern. A weak call: the adjudicator gave yes on a similar sentence in U7861. R01 is report-only and not in any metric. Direction: adjudicator-strict.

Caveats on the 0.90:
- Priming: `RESULTS.md`, read before judging, names three of the researcher's disagreements. U9207/H10 is the only one in this sample, so that cell is not blind. Without it, 39 cells give kappa 0.949 and positive agreement 0.974.
- Exposure: a glance at `verdicts_00.json` showed about 10 verdicts for U3972, so that unit was excluded from the pool before sampling.
- Borderline cells: the reviewer called several weak ones yes (U3920 and U5302 on C01, U5302 on C05, U7861 on R01). The adjudicator agreed on all of them, so it is not lenient on every weak call.
- Pooled over both checks (researcher 40, reviewer 39 new cells): n=79, kappa 0.871, positive agreement 0.925. Of 6 disagreements, 5 are adjudicator-lenient and 1 is adjudicator-strict (report-only item).

Sensitivity of the headline to the lenient direction (scratch copy; an `adjudication/override.json`, read by `src/analyze.py` when present, flipping the 4 cells the two checks flagged as adjudicator-yes/judge-no: U9207/H10, U8803/H06, U6404/H08, U2326/H02):
- recall_H A2-pre 0.602 → 0.580 (CI 0.511–0.648); floor-adjusted 0.329 → 0.307; ND 0.417 → 0.404 (CI 0.237–0.562).
- Ruling unchanged (CHANGE, borderline on the ND CI). "About 0.58–0.60 of the human findings" holds.

## 5. Label sensitivity (not in the protocol)

The ND discrimination figure depends heavily on which items count as "fixed". On a scratch copy, with everything else frozen and no override:

| labeling | ND | ND 95% CI | frozen-rule ruling |
|---|---|---|---|
| as committed | 0.417 | 0.246–0.571 | CHANGE (borderline) |
| C07 and C08 → partial (section 3) | 0.495 | 0.318–0.656 | **CONTINUE** |
| C07, C08, H04, H08, C09 → partial | 0.742 | 0.525–0.958 | **CONTINUE** |

The CI lower bound of 0.246 against the 0.25 threshold is the only thing that makes the ruling CHANGE. Two items whose "fix" leaves in place the problem described by their own match rule (C07, C08) are enough to move it. Nothing was edited: the labels were frozen before the run, and the protocol scores the committed bytes. "Borderline CHANGE" therefore means "point estimates meet CONTINUE; the CI is label-sensitive", not that the LLM pass failed the discrimination test.

## 6. Verdict

**Reproduced.** Hashes, `results.json`, `posthoc_topk.json` and the ruling match exactly. The blind judging check passes the protocol thresholds (kappa ≥ 0.70, positive agreement ≥ 0.75) independently of the researcher's own check, with the lenient direction confirmed on one cell. Numbers that change: none in the committed results. Numbers that move under alternatives: recall 0.60 → 0.58 if lenient cells are flipped, and the ruling flips to CONTINUE if C07 and C08 are relabelled (section 5).
