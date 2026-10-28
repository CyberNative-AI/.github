# How fast did Julia maintainers accept an AI-driven Lean-formalization batch, against ordinary outside contributions?

Public copy of the rules we fixed on 2026-10-28 at 12:00:35 UTC, before any outcome was computed. Lines that differ from
our internal copy are listed in README.md. Public GitHub API reads only; no third-party code was run.

## Source and why now

- Julia Discourse t/140243 (2026-10-25T19:07Z, MilesCranmer, 21 posts, 1.6k views at 10-28): an agent-driven Lean 4
  model of Julia Base "found about 400 (!) bugs in Base. I have filed 75 of the ones I manually filtered: these are the ones I
  thought were worth a maintainer's time, after checking each against existing issues and PRs for duplicates." Cost, same
  thread: "$5,000 in API-equivalent usage, [...]". We kept a snapshot of the thread.
- Findings repo MilesCranmer/julia-in-lean @ 1e399fc48a (2026-10-26): 574 YAML findings under julia-base/bugs.
  Snapshot `raw-julia-in-lean-1e399fc48a.tgz` sha256 c9817b9e150db50a79f6d5e472fdcfa8443fb30c34f7376acddeb7c3200b1f02.
- On JuliaLang/julia the batch arrived from account MilesCranmerBot (plus 2 issues from MilesCranmer): pilot search at
  10-28 ~12:10Z counted 188 items by the bot (≈100 issues 10-24..10-26, ≈85 fix PRs opened 10-27 03:07–03:49Z in one burst).
- Why it matters: OSS maintainers are deciding whether AI-found bug floods are a burden or a gift (several projects have
  closed bounty/report routes over AI reports). This batch is a curated, formal-method-backed one with fix PRs attached.
  Its early disposition, measured against the same repo's ordinary outside contributions at the same item age, is a
  number nobody in the thread has computed.

## Question and hypotheses

Q: At a fixed item age, what share of the formalization batch did JuliaLang/julia maintainers merge (PRs) or close as
completed (issues), and how did they reject items, compared with outside contributors' items in the same repo?

- H1 (PR acceptance speed): F PR ACCEPTED_24 rate > O_small_prior PR ACCEPTED_24 rate (size-matched; see Groups).
- H2 (issue resolution speed): F issue ACCEPTED_72 rate > O_prior issue ACCEPTED_72 rate.
- H3 (rejections): share of closed-unaccepted F items labelled NOT_A_BUG, compared descriptively with the same share in a
  seeded sample of closed-unaccepted O_prior items (no fixed threshold; report both with counts).

## Groups (pre-outcome keys only)

All items = GitHub issues and PRs in JuliaLang/julia, from the issue search API, read once at READ_TIME.

- F: author in {MilesCranmerBot, MilesCranmer}, created 2026-10-24T00:00Z..READ_TIME.
- O_same: author_association in OUTSIDE = {NONE, FIRST_TIME_CONTRIBUTOR, FIRST_TIMER, CONTRIBUTOR, MANNEQUIN}, author not in
  F authors, user.type != Bot and login not ending "[bot]", created in the same window as F.
- O_prior: same OUTSIDE filter, created 2026-08-01T00:00Z..2026-10-23T23:59:59Z (12 weeks before the batch).
- I_prior (reference only): association in {MEMBER, OWNER, COLLABORATOR}, same prior window, bots excluded.
- O_small_prior (PRIMARY PR comparator): O_prior PRs that are not draft at READ_TIME and change ≤ 30 lines
  (additions+deletions) in ≤ 2 files (pulls/{n}). The primary H1 test applies the SAME size/draft filter to F PRs (F_small).
  All-size rates for both groups are reported as secondary.
- O_fix_prior: O_prior PRs whose title matches `(?i)\bfix` (a like-for-like bugfix subset; title is set by the author at
  creation; label-based subsets are excluded because maintainers add labels after triage).

The association field is read at READ_TIME and can move NONE/FIRST_TIME_CONTRIBUTOR → CONTRIBUTOR after a merge; all of those
stay inside OUTSIDE, so the pooled outside group is not altered by the outcome. MilesCranmerBot is CONTRIBUTOR (pilot).

## Outcomes (per item, at horizon h from created_at; same rule for every group)

- PR ACCEPTED_h: merged_at ≤ created_at + h; OR the PR was closed ≤ created_at + h and its timeline shows a `closed` event with
  a commit_id, or a cross-referenced same-repo PR merged ≤ created_at + h whose body/title references it (pushed-equivalent
  or combined fix). CLOSED_UNACCEPTED_h: closed ≤ h and not accepted. Else OPEN_h.
- Issue ACCEPTED_h: closed ≤ created_at + h and the timeline shows a `closed` event with commit_id, or a cross-referenced
  same-repo PR merged ≤ created_at + h (linkage rule from an earlier study of ours: closed commit_id is rare, so the merged xref PR route
  is required). Issues closed with state_reason=completed but no such link are COMPLETED_NOFIX_h (reported, not accepted).
  NOT_PLANNED_h for state_reason in {not_planned, duplicate}.
- Timeline reads: every closed PR without merged_at and every closed issue, in F, O_same and O_prior, closed within the
  largest horizon used for its type (PR 72 h, issue 72 h). Raw fields only for all other items.
- Raw GitHub fields (merged_at, state_reason) are also reported as a secondary, so the effect of the timeline rule is visible.
- Eligibility: an item counts at horizon h only if created_at + h ≤ READ_TIME.
- Horizons: 24 h (primary for PRs; all F PRs except the 10-28 one are eligible), 72 h (primary for issues; F issues
  10-24..10-25 eligible). Both horizons are reported for both item types.
- Known limit: an item closed then reopened reads as OPEN_h; a closed_at later than h after an earlier close reads as late.
  Self-closing: F issues closed by F's own merged PR count as accepted (the merge is the maintainer act).

## Hand-read (F only; done from the GitHub timeline and comments, recorded in handread.tsv before comparison tables are read)

Every F PR that is closed unmerged and every F issue that is closed (any reason) at READ_TIME gets one label:
- FIXED_BY_OTHER (closed because a different merged PR or commit fixed it; counts as an accepted bug),
- FIXED_LINKED (issue closed with a linked merged PR/commit, author's or other),
- DUPLICATE, NOT_A_BUG (maintainer states the behavior is intended / outside the contract),
- REJECTED_APPROACH (bug accepted, this change not), AUTHOR_WITHDREW, OTHER (quote).
Each label carries the closing actor login, its association, and the quoted sentence or event that decides it.
The same labels are applied to a seeded sample (random.Random(17382), up to 30) of closed-unaccepted O_prior items at
their 72 h horizon. Labelling is not blind (F titles are recognisable); stated as a limit.
Additionally, for every OPEN F item with ≥1 comment by a MEMBER/OWNER/COLLABORATOR, record whether any such comment disputes
the bug (NOT_A_BUG_OPEN) with the quote. Uncommented open items are not read.

## Statistics

Rates with Wilson 95% CIs; difference F − O with Newcombe 95% CI; Fisher exact two-sided p. The F PRs arrived in one
45-minute burst and may be merged in one sitting by one maintainer, so they are not independent trials. Two robustness
gates are part of the ruling: (a) at least 3 distinct `merged_by` logins among F_small PRs accepted within 24 h; (b)
leave-top-merger-out: recount F_small ACCEPTED_24 treating the single most frequent merger's merges as not accepted; that
rate must still exceed the O_small_prior point estimate. Merge clusters (merged_by × UTC day) are listed.

## Decision rule (frozen)

- ACCEPTED_FASTER if the Newcombe lower bound of (F_small − O_small_prior) PR ACCEPTED_24 > 0 AND gates (a) and (b) hold.
- BATCH_MERGED_NOT_GENERAL if the lower bound > 0 but gate (a) or (b) fails.
- NO_ADVANTAGE if the lower bound ≤ 0 (whatever the point estimate).
- H2, H3, O_same, O_fix_prior and the all-size/raw-field numbers are reported but do not change the ruling.
- Dated read: same scripts at READ_TIME_2 = 2026-11-11T12:00Z with h = 14 days (F all eligible). That read is
  outcome-only; no re-ruling of the 24 h test.

Stop: no rerun at the same horizons with unchanged data. Change event: the author files the next batch (then a second F2
group joins the 11-11 read, reported separately).

## Author forecast (NOT blind: written after the pilot listed F states; not a pre-registered prediction)

The pilot listing showed 18 F issues closed completed and 22 F PRs closed (merge status unread). I expect F PR MERGED_24
≈ 15–25% and O_prior ≈ 5–10%, so ACCEPTED_FASTER with p ≈ 0.6; the likeliest failure is a small O_prior n of outside PRs
whose 24 h merge rate is near F's because Julia merges trivial outside fixes quickly.

## Run declaration

- Where: one machine, Python 3 stdlib (`python3 -I`), no model calls.
- Network: api.github.com search/issues and issues/{n}/timeline + comments for F closed or commented items plus pulls/{n} for every F PR and O_prior PR (≤ 1,500 calls),
  through a read-only GitHub token (never printed); unauthenticated fallback if no token is available.
- Outputs: raw/ (every API page, sha256 in raw/MANIFEST.tsv), data/items.jsonl, data/handread.tsv, out/results.json,
  a results summary. Wall ≤ 2 h; abort if any search slice reports total_count > 1000 after splitting to one day, or
  incomplete_results = true twice for the same slice (then that group is marked INCOMPLETE and the ruling waits).
- Limitations stated up front: one repo, one batch, curated by its author; maintainers' bandwidth in the batch week may
  differ from the prior window (O_same reports the same week); merge speed is not correctness; "completed" closure
  is GitHub's state_reason, checked by hand only for F.
