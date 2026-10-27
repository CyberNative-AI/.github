# Paying strangers for merged pull requests: what one program's year of PRs to open source projects shows (October 2026)

From October 2025 to October 2026, Gittensor, a subnet of the Bittensor crypto network, paid an
open pool of contributors, which it calls miners, in TAO, the network's token, for pull requests
merged into open source repositories on a list it kept in its own GitHub repository. On
October 12, 2026 it emptied the list ("burn all miner emissions (empty registry …)", commit
[`884ce17`](https://github.com/entrius/gittensor/commit/884ce1785f802f384b1f13a9df87ba29d9cbe821)).
We counted what those contributors' PRs did on GitHub.

**When a repository came off the paid list, miner PRs to it nearly stopped within a month.**
On April 9, 2026 the list dropped 1,207 repositories. We counted the 29 independent ones that had
miner PRs in the month before. Miner accounts opened 89 PRs to them in the 32 days before and 7 in
the 32 days after. Other PRs to the same repositories
held steady (12,416 before, 12,202 after). A second removal on May 12, counted the same way across 30 repositories, went from 446 to 11.

**Their PRs were merged less often than ordinary outside contributions to the same projects.**
Among miner accounts GitHub's search can find, 69.7% of 905 decided PRs opened before April 9, 2026
to 68 repositories were merged within 90 days, against 80.8% of 2,852 PRs from outside contributors to the same
repositories in the six months before the program.

The rules we wrote down before counting give no firm verdict on either question (see
[How sure we are](#how-sure-we-are)).

## Why now

The program stopped paying on October 12, so its whole run can now be counted. The one public
account of it we found is from a maintainer of sbt, the Scala build tool:
"[sbt and the miners of the wild west](https://www.eed3si9n.com/sbt-and-the-miners-of-the-wild-west/)"
(January 2026) and "[shutting down the goldmine](https://eed3si9n.com/shutting-down-the-goldmine/)"
(April 2026). Those posts describe one project. This note counts across all the independent
projects on the list.

## Results

"Independent" means the repository was on the first list (October 29, 2025) and its owner is not
one of the miners. "Miner" means an account in Gittensor's public miner list on October 26,
2026, or the author of a PR carrying the program's required line "Contribution by Gittensor".
"Decided" means merged or closed within 90 days of opening.

33 of the 182 registered miner accounts cannot be found with GitHub's `author:` search. PRs from
some of them (10 of the 33 in our two removal windows) do appear when a repository is searched as
a whole. The removal counts below include
them. The merge rates and the monthly table cover only the accounts search can find.

| Question | Miners | Comparison |
|---|---|---|
| PRs in the 32 days before → after the April 9 removal, the 29 removed independent repositories with miner PRs before it | 89 → 7 (accounts search can find: 74 → 1) | Other PRs to the same repositories: 12,416 → 12,202. Accounts search can find, 28 repositories still listed: 226 → 428 |
| PRs in the 32 days before → after the May 12 removal, the 30 removed independent repositories with miner PRs before it (ragflow left out, below) | 446 → 11 (accounts search can find: 381 → 11) | |
| PRs merged within 90 days, 68 independent repositories, accounts search can find, PRs opened before April 9, 2026 | 69.7% of 905 | 80.8% of 2,852 from outside contributors in the 6 months before the program |
| Accounts that cannot be found with GitHub's `author:` search | 33 of 182 | 4 of 182 outside contributors drawn at random from the comparison PRs; 2 of 182 drawn from PRs to the April 9 repositories in March–April 2026 |

The April 9 change was merged at 21:18 UTC on April 9; its commit is dated 16:39 UTC on
April 10. Six of the 7 later PRs were opened between those two times. Counting from April 10
instead gives 94 → 1. Either way, miner PRs to the removed repositories fell by more than 90%.

Ruff accounts for part of the April 9 drop: a Ruff maintainer said on March 30 that the project
would stop participating (below), and 17 of the 89 earlier PRs went to Ruff. Without Ruff, the count goes from
72 to 2.

The May 12 row leaves out infiniflow/ragflow, which was removed on May 12 and put back on the
list on May 19. With ragflow included, accounts search can find went from 435 to 204 PRs, 193 of
them to ragflow.

Just over half of the decided miner PRs in the merge-rate row went to three repositories:
langgenius/dify (232), sbt/sbt (139) and happyfish100/fastdfs (109).

Of the 33 accounts search cannot find, 30 still have a public profile page and 3 are deleted.
We do not know why the 30 are missing from search results.

### Ruff

Ruff, the Python linter, was on the April 9 removal list. On March 30, 2026, a Ruff maintainer
replying on [astral-sh/ruff#24239](https://github.com/astral-sh/ruff/pull/24239) to a contributor
whose own contributions they called "great", wrote: "we've seen many
other contributions that exhibited poor behavior, more than we did before we were added (without
being asked), which is why we decided to stop participating." On
[#24190](https://github.com/astral-sh/ruff/pull/24190): "I already reached out to have the
project removed." On issue [#24304](https://github.com/astral-sh/ruff/issues/24304): "we'll close all
PRs from accounts associated with them." #23350, #24048, #24190, #24239 and #24304 were closed.

We searched the other 28 counted repositories removed on April 9 for similar statements in issue and PR
text and comments and found none. The search only reads text GitHub's search matches, so it can
miss some.

### Where the paid merges went later

Merged miner PRs that were eligible for pay, by month merged and kind of repository (accounts
search can find):

| Month | Independent | Added to the list later, or owned by a miner | The PR author's own repository, or one where they are a member or collaborator |
|---|---|---|---|
| January 2026 | 204 | 16 | 40 |
| April 2026 | 305 | 289 | 120 |
| June 2026 | 79 | 6,798 | 2,286 |
| September 2026 | 2 | 40 | 88 |

From June 2026, almost none went to the independent projects.

## How sure we are

Before counting merges, we wrote down two tests with fixed thresholds, run on the accounts
search can find. Neither gave a verdict.

- **Merge rate: fragile.** The weighted gap is −11.0 percentage points. Our rule labelled a gap
  of −5 points or better ACCEPTED, −15 or worse LOWER, and anything between SIMILAR-LOWER, so it
  lands in the middle band. Leaving out dify, the largest repository (26% of the miner PRs),
  moves it to −16.3, into LOWER; leaving out the most active miner moves it to −12.9.
- **Work after pay stopped: underpowered.** The April 9 test needed at least 100 miner PRs in
  the window before the removal. The accounts search can find had 74. Our pre-set trend check
  also flags both removals (next section), so it would not have given a verdict with enough
  PRs either.

Everything else here, including the counts that add the accounts search cannot find, the May 12
removal, the Ruff statements and the monthly table, is exploratory: we looked at it after the
tests were set.

Things that cut the other way, or that we cannot rule out:

- Outside contributors who were not on the miner list also had PRs merged less often while the
  program ran. Against them, the miner gap is −1.5 points. Stricter review during the program,
  or miners we could not identify, would both explain that.
- Our pre-set trend check flags both removals; the trend was upward. Miner PRs to the removed
  repositories were growing before both removals: from the 32 days before that window to the
  window itself, they grew 4.3 and 1.9 times as fast as other PRs to the same repositories
  (accounts search can find).
- The merge rates leave out the 33 accounts search cannot find, and miners who left before
  October 2026. If their PRs were rejected more often, the true merge rate is lower than ours.
  In the April windows, the PRs we could find from the 33 were merged less often than the
  others at any time so far (7 merged, 12 closed without merging, 1 still open), but that is
  only 20 PRs from 5 accounts.
- GitHub reports whether an author is a member of a repository as of today, not as of the PR.
- This is one operator paying in one crypto token. It does not test bounties paid by projects
  themselves, grants, or paid work for a customer.

## Reproduce

All inputs are public:

- the list's history: 237 commits to
  [`gittensor/validator/weights/master_repositories.json`](https://github.com/entrius/gittensor/commits/main/gittensor/validator/weights/master_repositories.json);
- the miner list: `https://api.gittensor.io/miners` (we read it on October 26, 2026);
- PRs: GitHub's search API, `author:` and `"Contribution by Gittensor"` queries, created
  2025-04-01 to 2026-10-12, and repository-wide queries for the two removal windows.

[`reproduce/`](reproduce/) holds the collector, the analysis scripts, a public copy of the test
plan we wrote before counting with its three dated amendments (the README lists every line that
differs from our internal copy, with that copy's SHA-256), the second run's removal-window scripts, and
the per-repository counts behind every number above. It does not hold the per-account rows; the
collectors rebuild them from the sources above. See
[`reproduce/README.md`](reproduce/README.md).

We ran this twice on our own machine: a second, separate run re-derived the numbers from the
first run's data (taking the lists of removed repositories as given) and re-pulled both removal
windows from GitHub. Nobody outside the company has
reproduced it.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai. We will publish dated corrections here.
