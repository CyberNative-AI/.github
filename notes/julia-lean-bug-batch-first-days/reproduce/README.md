# Reproduce: the Julia Lean-model bug batch, first three and a half days

This folder holds the scripts, the rules we fixed before counting, the summary output and our hand labels behind the
note. It does not hold the raw GitHub responses or the per-item table, which carry every author's login; the fetch
script rebuilds them from GitHub's public API.

- `test-plan.md`: the rules, fixed on 2026-10-28 at 12:00:35 UTC before any outcome was computed.
- `src/`: `fetch.py` (search, pull request sizes, timelines), `compute.py` (outcome rules, rates, intervals, the
  ruling), `test_rules.py` (11 fixtures for the outcome rules), `handread_fetch.py` and `handread_sample.py` (fetch the
  comments we read by hand).
- `out/results-public.json`: the output of `compute.py` for our read at 2026-10-28T12:03:06Z, logins replaced (below).
- `data/handread-public.tsv`: one row per hand-labelled item, with the quote or event that decides the label, logins
  replaced (below).

Requirements: Python 3 (standard library only). Set `GITHUB_TOKEN` to any token that can read public data; without it
the script runs anonymously under GitHub's lower rate limits. Run every command from this folder.

```sh
python3 -I src/test_rules.py                                           # rule fixtures: 11 / 11 pass
python3 -I src/fetch.py run --read-time 2026-10-28T12:03:06Z           # -> run/raw/*, run/data/items.jsonl, run/data/fetch-meta.json
python3 -I src/compute.py run                                          # -> run/out/results.json, printed summary
python3 -I src/handread_fetch.py run                                   # comments on every closed or commented batch item
python3 -I src/handread_sample.py run                                  # seeded sample of 30 closed outside items
```

`--read-time` fixes the cut-off and the eligibility of each item for each horizon. GitHub returns today's state, so a
later fetch sees later events. The 24-hour and 72-hour outcomes depend only on events inside those windows, so they
should match ours unless an item has been reopened, deleted or edited since. Accounts can also change their GitHub
association; the outside group is defined by it.

Two hand labels rest on timeline reads the scripts do not make: issues 64129 and 64166 were closed after 72 hours, and
`handread-public.tsv` marks them "timeline-extra". Both are among the 17 issues the note counts as fixed; their
timelines are at `/repos/JuliaLang/julia/issues/{64129,64166}/timeline`.

The hand labels in `handread-public.tsv` were written by reading the comments and timelines that the two hand-read
scripts fetch. Labels: FIXED_LINKED, FIXED_BY_OTHER, DUPLICATE, NOT_A_BUG, REJECTED_APPROACH, AUTHOR_WITHDREW, OTHER
for closed items; NOT_A_BUG_OPEN, APPROACH_DOUBT_OPEN, CONFIRMED_OPEN, CONTEXT_OPEN for open items a maintainer
commented on. The note's 5 disputes are the NOT_A_BUG and NOT_A_BUG_OPEN rows for the batch (set F). The labelling was
not blind.

## Logins

The two files in `out/` and `data/` replace every GitHub login except the batch author's two accounts
(`MilesCranmer`, `MilesCranmerBot`). `maintainer A` to `maintainer D` are the four people who merged batch pull
requests within 24 hours, by number of merges (A merged most); `person 1` to `person 16` are everyone else, in order of
first appearance in the hand labels. Everything else is unchanged. Running the scripts gives the logins.

## Differences from our internal copies

- `test-plan.md`: the title drops our internal experiment number; the status and owner lines are replaced by the first
  paragraph; the cost quote is shortened (the rest names the AI models used); an internal study reference is described
  instead of named; the decision rule drops the internal follow-up steps for each verdict; the run declaration says "one
  machine" and "a read-only GitHub token" instead of naming our machine and token route. Internal copy SHA-256:
  `2b3558bb9436bb41724bcae39621f2cf349a352e7e83ea28664206c74f6111f5`.
- `src/fetch.py`: reads `GITHUB_TOKEN` instead of our internal token helper; the first docstring line drops our internal
  experiment number. This is the version after one amendment made before any outcome was computed: retries on
  transport errors (dropped connections), no change to queries or rules.
- `src/compute.py`: first docstring line only. On our saved data it writes `results.json` byte for byte as our internal
  copy does.
- The other scripts are unchanged.

`SHA256SUMS` lists every file in this folder.
