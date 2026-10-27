# Reproduce: what Gittensor bought by paying strangers for merged PRs

This folder holds the scripts, the test plan and the per-repository counts behind the note. It does not hold
per-account rows (PR lists with GitHub logins, the miner list, the list of accounts hidden from search). The
collectors below rebuild them from public sources into `raw/`.

- `test-plan.md`: the rules we fixed on 2026-10-26 before counting merge states, and three dated amendments.
- `src/`: the collector and analysis scripts (first run) and the removal-window scripts (second run).
- `out/`: the outputs the note's numbers come from.

Requirements: Python 3 (standard library only; we used 3.14) and git. Run every command from this folder. Set
`GITHUB_TOKEN` to any GitHub token that can read public data; without it the scripts run anonymously under
GitHub's lower search rate limit and spend much of their time waiting. The collector waits 2.2 s between search
calls and stops at 4,000.

## Commands, in order

```sh
mkdir -p raw/removal
# 1. registry history: all 237 commits to the paid-repository list in entrius/gittensor, up to 884ce17
python3 src/fetch_registry.py gittensor          # -> raw/whitelist_commits.json, raw/wl/<sha>.json
python3 src/registry.py                          # -> out/registry.json (intervals per repo, cut 1 and cut 2 lists)
# 2. miner list (we read it on 2026-10-26: 182 githubUsername values; it may have changed since)
curl -s https://api.gittensor.io/miners -o raw/api_miners.json
# 3. collector, first stages: tagline PRs, then every PR by each miner and tagline author, 2025-04-01..2026-10-12
python3 src/collect.py tag miners                # -> raw/tag_prs.jsonl, raw/miner_prs.jsonl, raw/calls.jsonl
python3 src/unsearchable.py --check-accounts     # -> raw/unsearchable_accounts.json (--check-accounts asks /users; hidden_accounts.py needs it)
# 4. collector, last stages: H1 baseline, H2 repo-activity counts and the ban screen
python3 src/collect.py baseline counts           # -> out/baseline_repos.json, out/cut*_count_repos.json, raw/baseline_*_prs.jsonl, raw/ban_screen.jsonl
# 5. E4 control: 182 outside authors from the baseline (seed 16784), same author: search probe
python3 src/e4_control.py                        # -> raw/e4_control_logins.json, out/e4_control.json
# 6. analysis
python3 src/analyze.py                           # -> out/results.json, out/ban_candidates.json
python3 src/posthoc.py                           # -> out/posthoc.json
# 7. removal windows (second run): every PR in each removed repo, 32 days before and after each removal
C1=$(python3 -c "import json; print(','.join(json.load(open('out/cut1_dropped_count_repos.json'))['repos']))")
C2=$(python3 -c "import json; print(','.join(r for r in json.load(open('out/cut2_dropped_count_repos.json'))['repos'] if r != 'infiniflow/ragflow'))")
python3 src/pull.py raw/removal/cut1_pre.jsonl  "$C1" 2026-03-08T21:18:56Z 2026-04-09T21:18:55Z
python3 src/pull.py raw/removal/cut1_post.jsonl "$C1" 2026-04-09T21:18:56Z 2026-05-11T21:18:55Z
python3 src/pull.py raw/removal/cut2_pre.jsonl  "$C2" 2026-04-10T20:43:25Z 2026-05-12T20:43:24Z
python3 src/pull.py raw/removal/cut2_post.jsonl "$C2" 2026-05-12T20:43:25Z 2026-06-13T20:43:24Z
python3 src/removal_windows.py                   # -> out/removal_windows.json
python3 src/analyze_pull.py raw/removal/cut1_pre.jsonl raw/removal/cut1_post.jsonl   # optional summary per frame
python3 src/hidden_accounts.py                   # -> out/hidden_accounts.json (offline)
# 8. April control (second run): 182 outside authors from the cut-1 pre-window pull (seed 16784), same author: search probe
python3 src/april_control.py                     # -> raw/april_control_logins.json, out/april_control.json
```

`analyze.py` needs `out/ban_labels.json` and stops if a ban-screen candidate repository has no label. We wrote
those labels by hand-reading each candidate's hits after collection and before the H2 numbers were printed; the
labeller knew the hypothesis. `collect.py` keeps every search response in `raw/calls.jsonl` and answers repeated
calls from it, so a stopped run resumes where it stopped, and `analyze.py` and `posthoc.py` make no new calls.

**Search calls, roughly:** the collector made 1,330 (1,292 answered; 38 were HTTP 422 for accounts search cannot
find), E4 made 182, the four removal-window pulls made about 620, and the April control made 182. That is about 2,300
in all, at about 27 a minute. `unsearchable.py --check-accounts` and the April control also ask `/users` once per
hidden account (33 and 2 calls in our runs).

## What each output holds

| file | contents |
|---|---|
| `out/results.json` | The ruled numbers. H1: qualifying repositories, weighted and median difference in merge rate (miners minus outside baseline), leave-top-repository-out and leave-top-miner-out values, pooled rates, the in-program baseline, recruited vs existing pairs. H2: PR counts per window (`N_m` miners, `N_c` other PRs), ratio and placebo for cut 1, the still-listed comparison repositories and cut 2; ban-screen result. Exploratory E2 (merged miner PRs by month and repository class) and E3. |
| `out/posthoc.json` | Post-hoc numbers: cut 1 and cut 2 without repositories re-listed inside the post window (cut 2 without infiniflow/ragflow: 381 → 11), the top repositories, and the E4 counts (33 of 182 registered accounts hidden from search; 4 of 182 control accounts). |
| `out/e4_control.json` | The E4 probe result for each control account: `ok` or `422`. Logins are replaced by their position in the sorted sample (`c001`..`c182`); `e4_control.py` writes the logins to `raw/`. |
| `out/baseline_repos.json` | The 79 repositories whose pre-program outside PRs form the H1 baseline. |
| `out/cut1_dropped_count_repos.json`, `out/cut1_stayed_count_repos.json`, `out/cut2_dropped_count_repos.json` | For each removal: the three 32-day windows and the repositories counted (removed or still listed, independent, with at least one miner PR in the window before). |
| `out/ban_labels.json` | Our ban-screen labels, one per candidate repository. |
| `out/removal_windows.json` | Second run, exploratory. Per repository and per window (32 days before and after): all PRs, PRs in the complete frame (registered miners plus all Gittensor-tagline authors), PRs in the search-visible frame (the first run's frame), and other PRs. Cut 1: 29 repositories, 89 → 7 complete, 74 → 1 search-visible, other PRs 12,416 → 12,202; without astral-sh/ruff 72 → 2; dated from the commit's committer date (2026-04-10T16:39:31Z) instead of its author date, 94 → 1 (that post window ends with the pull, 19 h short of 32 days). Cut 2: 30 repositories without infiniflow/ragflow, 446 → 11 complete, 381 → 11 search-visible. The frame definitions are in the file. |
| `out/hidden_accounts.json` | Second run, counts only. The 33 registered accounts `author:` search cannot find: 30 still have a `/users` profile, 3 return 404. Per removal window (as in `removal_windows.json`), how many of the 33 have PRs there, with PR count and merge state at pull time: cut 1, before or after, 20 PRs from 5 accounts (7 merged, 12 closed without merging, 1 open); cut 2, before or after, 54 PRs from 9 accounts; 10 of the 33 in either cut's windows, 4 in both. |
| `out/april_control.json` | Second run. The probe result for 182 outside authors drawn from the 2,306 eligible authors of PRs to the 29 cut-1 repositories in the 32 days before April 9, 2026: 180 `ok`, 2 HTTP 422 whose accounts still exist. The draw rule and eligibility are in `april_control.py`. Logins are replaced by their position in the sorted sample (`a001`..`a182`); the script writes the logins to `raw/`. |

Not included, because they list individual GitHub accounts: `raw/` (PR rows, miner list, hidden-account list,
E4 and April-control logins, pulls), `out/registry.json` (some listed repositories are owned by miner accounts; `registry.py`
rebuilds it) and `out/ban_candidates.json` (`analyze.py` rebuilds it).

## What we checked, and what a fresh run will give

We checked this folder offline against our own run. With our private `raw/` in place and the network blocked,
`fetch_registry.py` on a local clone, `registry.py`, `collect.py baseline counts`, `e4_control.py --from-logins`,
`analyze.py`, `posthoc.py` and `removal_windows.py` regenerated every file in `out/` byte for byte, and no new
search call was made. `hidden_accounts.py` and `april_control.py --from-logins` (fed the second run's probe result
file unchanged) wrote the two second-run count files the same way, and `--draw-only` returned the second run's sample. That is our own execution, not an independent reproduction.

A fresh run against GitHub today will not match byte for byte. Accounts get hidden or deleted, PRs change state,
and the miner list changes. Repo-wide search found PRs from accounts that `author:` search hides, which is why the
second run counts both frames.

## Changes from the internal copy

`test-plan.md` is a copy of our internal test plan (`PROTOCOL.md`) and its three amendments. The scripts in `src/`
are copies of the scripts we ran. Every line that differs is listed below. Line numbers refer to the internal files.

| file | line | kind |
|---|---|---|
| `PROTOCOL.md` | 1 | internal ID removed (title) |
| `PROTOCOL.md` | 3–4 | left out (status line with internal IDs and file names; internal risk label) |
| `PROTOCOL.md` | 6–28 | section left out (why we asked) |
| `PROTOCOL.md` | 29–36 | section left out (what decision of ours the result would change) |
| `PROTOCOL.md` | 68–69 | wording changed |
| `PROTOCOL.md` | 106 | label renamed (H2 outcome label, now LOW-PERSISTENCE) |
| `PROTOCOL.md` | 123 | label renamed (same label in the forecast) |
| `PROTOCOL.md` | 125–133 | section left out (what we would do after each outcome) |
| `PROTOCOL.md` | 137 | internal ID removed (how our token was obtained) |
| `PROTOCOL.md` | 141 | internal ID removed (internal launcher) |
| `PROTOCOL.md` | 142 | internal ID removed (internal folder name) |
| `AMENDMENT-01.md` | 7–8 | wording changed |
| `AMENDMENT-01.md`, `AMENDMENT-02.md`, `AMENDMENT-03.md` | 1 | heading level only |
| `src/analyze.py` | 1, 140 | internal ID removed (docstring); wording changed (comment) |
| `src/analyze.py` | 33 | label renamed (same H2 label; it appears in no `out/` file) |
| `src/collect.py`, `src/posthoc.py`, `src/registry.py` | 1 | internal ID removed / wording changed (docstring) |
| `src/gh.py` | all | rewritten: token from `GITHUB_TOKEN` instead of an internal credential helper; same retry and rate-limit rules |
| `src/e4_control.py` | 1–2, 10–15 | `--draw-only` and `--from-logins` modes added; public output keyed by sample position; same seeded draw |

`src/analyze_pull.py` and `src/pull.py` are the second run's scripts with internal paths replaced by arguments and
`src/gh.py`; `analyze_pull.py` also renames one printed key, and `pull.py` counts its calls in memory. `src/fetch_registry.py`, `src/unsearchable.py`, `src/removal_windows.py` and `src/hidden_accounts.py` were written for this folder.
`src/april_control.py` is the second run's probe script with internal paths replaced by `src/gh.py` and fixed
`raw/` paths; the draw rule and the `--draw-only`, `--from-logins` and by-position public output were added. The
second run did not record how it drew its sample. We recovered the rule afterwards, and it rebuilds that sample
exactly: the same 182 logins in the same order.

The internal file's SHA-256 is 2b5f608bf060a1aaf5a6f7e9c35f455799e23d5d9d225b45f10dc4d3112a5c2a; this copy is not byte-identical to it.

## License

Our scripts, test plan and README are MIT licensed (`LICENSE`). The data in `out/` are counts derived from public
GitHub and Gittensor data.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai.
`SHA256SUMS` lists every file in this folder.
