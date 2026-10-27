Fixed on 2026-10-26 before merge states were counted. This public copy leaves out the sections on whether we would run a paid-contributor program of our own, removes internal identifiers, and changes the lines listed in README.md. We did not publish the plan or its hash at the time, so the order of plan and counts rests on our word.

# Test plan: what an open paid contributor collective actually bought (Gittensor SN74 natural experiment)

## Frame (frozen before any merge state is counted)

- Registry intervals: for every repo, the set of [added, removed) intervals from the 237 registry commits,
  in commit order (2 commits on 2025-11-21 have invalid JSON: carry the previous state forward).
- Miner set M = M_api ∪ M_tag.
  - M_api: the 182 `githubUsername` values in `https://api.gittensor.io/miners` (fetched 2026-10-26,
    `raw/api_miners.json`). These are miners registered at the end; earlier leavers are missing
    (survivorship, stated as a limitation).
  - M_tag: authors of all PRs whose body contains the required tagline "Contribution by Gittensor"
    (constant `PR_TAGLINE_PREFIX`, v3.0.0), collected in full (822 at pilot).
- PR rows: every PR authored by a member of M created 2025-04-01..2026-10-12 (GitHub search, window split
  recursively until each slice returns < 1,000). Fields kept: repo, number, author, author_association,
  created_at, closed_at, merged_at, state, tagline flag. Bots excluded (login ends `[bot]`).
- Independent repo (pre-outcome key): present in the first registry list (2025-10-29, built before any
  miner could lobby for additions) AND repo owner ∉ M. Everything else is "ecosystem/later".
- A miner PR is **paid-eligible** when its created_at falls inside one of its repo's registry intervals.

## H1 — acceptance (is incentive-recruited work accepted at the normal outside rate?)

Units: paid-eligible miner PRs to independent repos created before cut 1 (< 2026-04-09T21:18:56Z),
author_association ∉ {OWNER, MEMBER, COLLABORATOR}, not drafts.

Equal decision horizon (both arms): a PR is *merged90* if merged_at − created_at ≤ 90 d, *rejected90* if
closed unmerged with closed_at − created_at ≤ 90 d. Merge rate = merged90 / (merged90 + rejected90).
Secondary: merged90 / all created.

Primary baseline (pre-program, so no unidentified early miners): for each independent repo with ≥ 3
decided90 miner PRs (if > 400 repos, a seeded random 400, seed 16784), one search page (100,
`sort=created desc`) of closed PRs created 2025-04-01..2025-09-27. Keep authors ∉ M, not bots,
association ∈ {NONE, FIRST_TIMER, FIRST_TIME_CONTRIBUTOR, CONTRIBUTOR}. (Association is the current value,
not the value at PR time; both arms share this bias.) Secondary baseline: the same query inside the repo's
first registry interval clipped to < 2026-04-09T21:18:56Z (in-program; can be lowered by stricter review
during the program or contaminated by unregistered miners).

Statistic: for repos with ≥ 3 decided90 miner PRs and ≥ 5 decided90 baseline PRs, d_r = m_r − b_r.
Primary = mean d_r weighted by miner decided90 PRs; also unweighted median d_r, pooled rates,
leave-top-repo-out and leave-top-miner-out (by decided90 count) recomputations. Stratified report:
recruited miner–repo pairs (miner had no PR to that repo created before 2025-10-29; miner rows are
collected from 2025-04-01) vs existing contributors.

Rule (needs ≥ 30 qualifying repos, else H1 UNDERPOWERED):
- ACCEPTED: weighted d ≥ −0.05
- LOWER: weighted d ≤ −0.15
- SIMILAR-LOWER otherwise.
A ruling holds only if leave-top-repo-out and leave-top-miner-out give the same branch; otherwise
report FRAGILE with both values.

## H2 — persistence (does the work continue after pay stops?)

Natural experiment: cut 1, commit faa56734 (T1 = 2026-04-09T21:18:56Z), dropped 1,207 repos.
D1 = independent repos on the list immediately before faa56734 and absent immediately after.
Windows of 32 days, so the post window ends before cut 2 (2026-05-12) when the stayers also lost pay:
pre-pre = [T1−64d, T1−32d), pre = [T1−32d, T1), post = [T1, T1+32d).

- Recruited pairs only (primary): miner–repo pairs where the miner had no PR to that repo created before
  2025-10-29. Existing-contributor pairs are reported separately.
- N_m(w): PRs by M (recruited pairs) to D1 repos created in window w.
- Repo-activity control N_c(w): for each D1 repo with ≥ 1 miner PR in pre, search `total_count` of all PRs
  created in w minus that repo's PRs by M in w.
- R_m = N_m(post)/N_m(pre); R_c = ΣN_c(post)/ΣN_c(pre); primary = R_m / R_c.
- Pre-trend placebo: the same ratio for pre-pre → pre. If it falls outside [0.70, 1.43], H2 is CONFOUNDED
  (the drop was already under way, or the cut selected declining repos).
- Ban screen: for each counted D1 repo, `repo:{r} gittensor created:<T1`; repos whose hits contain a
  ban/policy/complaint about Gittensor are a stratum; primary is recomputed without them and must keep its
  branch, else FRAGILE.
- Comparison group (secondary): independent repos still listed after faa56734, same windows and statistic;
  report D1 ratio / stayer ratio when ≥ 10 stayer repos have a pre miner PR.

Rule (needs N_m(pre) ≥ 100 across ≥ 20 repos and ≥ 10 miners, else H2 UNDERPOWERED; CONFOUNDED overrides):
- LOW-PERSISTENCE: R_m/R_c ≤ 0.30
- DURABLE: R_m/R_c ≥ 0.70
- PARTIAL otherwise.
Same leave-top-repo/miner-out FRAGILE rule. Secondary: share of recruited miners with ≥ 3 pre PRs to D1 who
opened ≥ 1 post PR to D1. Cut 2 (73c9d034, 2026-05-12, 208 repos) is reported the same way (32-day windows)
as a secondary replicate without stayers.

## Exploratory (not ruled)

- E1 maintainer reactions: issues/PRs mentioning "gittensor" in repos not owned by M or entrius/opentensor;
  count repos with a policy, ban or complaint text and quote ≤ 3 primary passages.
- E2 where the money went: monthly share of merged miner PRs going to independent vs ecosystem/later vs
  self-owned repos.
- E3 self-merge share: decided miner PRs with association OWNER/MEMBER/COLLABORATOR.

## Author forecast (calibration record, written before outcomes)

H1: LOWER 0.50, SIMILAR-LOWER 0.30, ACCEPTED 0.20. H2: LOW-PERSISTENCE 0.70, PARTIAL 0.25, DURABLE 0.05.

## Limits, aborts, reproduction

- Network: GitHub REST search (token via `src/gh.py`, anonymous fallback), ≤ 28 search
  calls/min (sleep ≥ 2.2 s), ≤ 4,000 search calls total, ≤ 3 h wall, CPU only, $0.
- Abort → INVALID: > 5% of search calls end in an error after retries, or > 5% return
  `incomplete_results: true`.
- Runner appends JSONL and resumes.
- Privacy: GitHub logins are public pseudonyms; raw rows stay private; any public output
  reports aggregates and repo names only, no miner logins.
- Reproduce: `python3 src/collect.py` then `python3 src/analyze.py` (writes `out/results.json`).

## AMENDMENT-01 (2026-10-26, during collection, before any merge-state tally)

Observed: 34 of 182 M_api logins return HTTP 422 "The listed users cannot be searched either because the users do
not exist or you do not have permission to view the users" for every author: search (also anonymously; the pilot
counts in raw/pilot_miner_pr_counts.json held 422 as a value, so the pilot "53,027 PRs" was wrong: 39,101 for the
148 searchable logins). Account checks (raw/unsearchable_accounts.json): 3 deleted (/users and /user/{id} 404);
31 exist with public profile pages (HTTP 200) but are excluded from search. We do not know why GitHub
search excludes them.

Changes:
1. Frame: these 34 logins contribute no PR rows (their PRs are not visible to search). H1/H2 are therefore
   scoped to searchable accounts; if hidden accounts' PRs were mostly rejected, H1 is biased toward ACCEPTED
   (stated as a limitation in the result).
2. Abort counter: a per-login 422 of this kind is a frame exclusion, not an instrument error; the >5% INVALID
   rule counts all other errors.
3. New exploratory E4 (not ruled): share of searchable-hidden accounts among M_api (31/182 live + 3 deleted)
   vs a control of up to 182 distinct outside authors drawn (seed 16784) from the pre-program baseline rows,
   checked with the same author: search probe after collection. Recorded before the control is drawn.

## AMENDMENT-02 (2026-10-26 17:12Z, instrument only, before any tally)

Run 1 of the collector died at 17:09:47Z on a transient DNS error (`URLError [Errno -2] Name or service not known`)
raised from `gh.get`, which catches only HTTPError. `collect.search` now catches OSError/TimeoutError, records the
attempt as an error, waits 30 s and retries (max 4 attempts as before). No frame, window, rule or analysis change.
Resume uses the cached calls in raw/calls.jsonl and raw/miners_done.txt; the partially collected miner is replayed
from cache. Failed network attempts that eventually succeed are not logged as errors (only the final outcome is).

## AMENDMENT-03 (2026-10-26, erratum + post-result notes; analysis below is exploratory)

1. Erratum to AMENDMENT-01: 33 (not 34) of 182 M_api logins are unsearchable: 30 live with public profiles + 3 deleted
   (raw/unsearchable_accounts.json). The 34th pilot error was a single HTTP 403 (rate limit); that login was searched
   successfully in the main run. Main run: 38 per-login 422s = 33 M_api + 5 tagline-only authors.
2. Frame flaw found after results: the cut-2 secondary did not exclude repos re-added to the registry inside the post
   window. infiniflow/ragflow was re-listed 2026-05-19..06-23 and carries 193/204 post PRs. Cut 1 has no re-listed repo.
   Exclusion-corrected numbers are in out/posthoc.json (src/posthoc.py) and are labelled post hoc.
3. Ban-screen labels were written by the producer after collection, before H2 numbers were printed (out/ban_labels_receipt.md).
