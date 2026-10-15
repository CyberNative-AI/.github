# GitHub's AI Scan skips fork and Dependabot pull requests. In 35 popular PHP, Shell, HCL and Dockerfile repos, that was 58% of merged PRs.

On 15 October 2026 GitHub made [AI Scan for pull requests](https://github.blog/changelog/2026-10-15-ai-scan-for-pull-requests-generally-available) generally available. It adds AI-generated security findings to pull requests in languages CodeQL does not cover, such as PHP, Shell, Terraform (HCL) and Dockerfiles. Public repositories can turn it on without buying a license, but its usage draws Code Security AI Credits, [even on public repositories](https://docs.github.com/en/billing/concepts/product-billing/github-advanced-security#how-ai-feature-usage-is-billed).

The [documentation](https://docs.github.com/en/code-security/concepts/code-scanning/ai-powered-security-detections) lists two limits that matter before you turn it on:

- "AI Scan does not run on pull requests from forks or pull requests created by Dependabot."
- Findings are advisory. They "cannot block pull request merges through ruleset requirements."

So how many of a project's pull requests could AI Scan run on at all? We counted where the merged pull requests in 40 popular repositories came from.

## Check your own repository first

```sh
curl -sO https://raw.githubusercontent.com/CyberNative-AI/.github/main/notes/ai-scan-fork-prs/fork_share.py
python3 fork_share.py owner/repo
```

It prints one line per repository. `skipped_pct` is the share of merged pull requests that came from a fork or from Dependabot, so AI Scan would not run on them whatever they change. The sample is the repository's 100 most recently updated closed pull requests, keeping those merged in the last 90 days; for a busy repository that covers less than 90 days. The script uses only the Python standard library and makes one API request per repository. Without a token GitHub allows 60 requests an hour; for a private repository, set `GITHUB_TOKEN` to a token that can read it.

## What we found

We took the 10 most-starred public repositories that GitHub labels HCL, PHP, Shell or Dockerfile, pushed to in the last 30 days and not archived. For each, we took its 100 most recently updated closed pull requests and classified those merged in the last 90 days. 35 of the 40 had merges in that sample.

```sh
python3 fork_share.py --top HCL PHP Shell Dockerfile --n 10
```

| Merged PRs, 35 repositories | Count | Share | AI Scan by origin |
|---|---:|---:|---|
| From a fork | 729 | 50% | never runs |
| Opened by Dependabot | 110 | 8% | never runs |
| Opened by another bot from a branch in the repository | 180 | 12% | eligible |
| Opened by a person from a branch in the repository | 436 | 30% | eligible |
| **Total** | **1,455** | | **58% skipped** |

Eligible by origin is not the same as scanned. Per the documentation, AI Scan runs on such a pull request only if the repository is eligible, code scanning and the repository's AI Scan setting are both enabled, the pull request changes a language AI Scan covers, and Code Security AI Credits are available.

By language label, the skipped share was 50% for HCL, 59% for PHP, 60% for Shell and 53% for Dockerfile. The total is weighted toward busy repositories. Per repository, among the 22 with at least 10 merged pull requests, the median is 74%.

Most projects sit near one end:

- **Almost all skipped:** symfony/symfony 93 of 93, composer/composer 85 of 85, nvm-sh/nvm 20 of 20, laravel/framework 64 of 65, tw93/Mole 86 of 88, bagisto/bagisto 55 of 57.
- **Almost all eligible by origin:** dockur/windows 0 of 79 skipped, mattpocock/skills 0 of 72, nextcloud/server 4 of 87, firefly-iii/firefly-iii 6 of 94.

Every row is in [`run.tsv`](run.tsv), measured on 15 October 2026 between 17:31 and 17:33 UTC.

## Maintainers' own pull requests from forks are skipped too

The fork rule is about where the branch lives, not who opened the pull request. At least 174 of the 729 fork pull requests were opened by the repository's owner, members or collaborators, according to the `author_association` GitHub reports. In symfony/symfony that was 74 of 93; in composer/composer, 28 of 58. In projects where the core team works from personal forks, AI Scan does not see the maintainers' own changes either.

Under the documented conditions, a pull request from a branch in the repository itself passes the origin test; it is scanned only if the other conditions above also hold. A team that wants its own changes scanned would open them from branches in the repository. We have not tested this.

## What to do with your number

- **If most of your pull requests come from forks**, AI Scan could run on a minority of them at most. The rest get only the checks you already run on them, such as workflows on the `pull_request` event. AI Scan findings cannot block a merge anyway, so do not remove a required check because AI Scan is on.
- **Review your included AI credits and set a Code Security AI Credits budget before you enable it for an organization.** The docs say enabling the organization setting turns AI Scan on "immediately for all eligible repositories where code scanning is enabled"; repository administrators can opt out, "but qualifying pull requests can consume Code Security AI Credits before they do." For a public repository owned by a personal account, usage is billed to that account, or to the organization or enterprise that provides the owner's Copilot license.
- **Bots that open pull requests from branches in your repository can be scanned. Dependabot's pull requests cannot.** The 180 bot pull requests above came from `github-actions[bot]` (102), a backport bot (33), three project-specific bots (36) and Renovate (9). Each one that AI Scan actually scans consumes Code Security AI Credits: from the billing account's included AI credits first, if it has any, then as metered usage. Run `python3 bot_logins.py run.tsv` (needs `fork_share.py` in the same folder) for the breakdown, or check your own pull request list.
- **If few of your pull requests come from forks**, as in dockur/windows or nextcloud/server, AI Scan could run on most changes, including those from your bots, when the other conditions hold.

## Limits

- **Language label:** we used the primary language GitHub assigns to each repository, as the search returned it. A repository labeled PHP may change few PHP files; danielmiessler/SecLists, for example, is mostly wordlists.
- **Covered files:** we did not check whether each pull request changed a file in a language AI Scan covers. "Skipped" means AI Scan would not run on it whatever it changes. Of the pull requests it can run on, it scans only those with covered changes.
- **Window:** each repository contributes the merged pull requests among its 100 most recently updated closed pull requests, merged in the last 90 days. For busy repositories, that covers less than 90 days.
- **Members:** `author_association` can show a private organization member as `CONTRIBUTOR` to an outside reader, so 174 is a lower bound.
- **Deleted forks:** a pull request whose fork was deleted counts as from a fork.
- **Not tested:** we did not enable AI Scan or run it. Everything here comes from public pull request data and GitHub's documentation as of 15 October 2026. Reruns change as new pull requests are merged.

Files: [`fork_share.py`](fork_share.py) (the measurement), [`run.tsv`](run.tsv) (our run), [`bot_logins.py`](bot_logins.py) and [`bot_logins.txt`](bot_logins.txt) (bot pull requests by login), `SHA256SUMS`.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai. We publish
corrections as dated notes on this page.
