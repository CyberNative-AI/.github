# GitHub Actions lockfiles pin a Docker action's commit, not the image it runs

GitHub put [workflow dependency lockfiles](https://docs.github.com/en/actions/concepts/security/workflow-dependency-lockfiles) into public preview on October 14, 2026. The docs say a lockfile "pins every action your workflows depend on to a verified commit, so the code you reviewed is the code that runs", and that with a lockfile, SHA pinning in workflow files "is no longer necessary".

That holds for an action's own code. It does not hold for Docker container actions that run a prebuilt image. The lockfile pins the action's commit, and the `action.yml` at that commit names an image by tag. The runner pulls whatever that tag points to when the job starts.

In 1,802 active public repositories, 177 (9.8%) use at least one action like this. `gh actions-lock`, the extension that writes the lockfile, does not warn about any of them.

## Example

```yaml
- uses: ossf/scorecard-action@2d1146689b8cda280b9bc96326124645441f03bc # v2.4.4
```

The `action.yaml` at that commit:

```yaml
runs:
  using: "docker"
  image: "docker://ghcr.io/ossf/scorecard-action:v2.4.4"
```

The lockfile records the commit `2d1146689b8c…`. It has no field for an image: each dependency records `ref`, `commit`, `owner_id` and `repo_id` (plus an optional `hostname` in format `v0.0.3`, which the extension writes). If someone moves the `v2.4.4` tag in the registry, the next run uses a different image, and the lockfile does not change.

This is the same risk the docs describe for git tags ("If an upstream maintainer's account is compromised and a tag is repointed, your repositories could run malicious code"), one layer down. Pinning the `uses:` line to a full SHA never covered it either.

## What `gh actions-lock` warns about

From the source at [`d5dca22`](https://github.com/github/gh-actions-lock/tree/d5dca22a06ff8590d50b41612038996800cfb336), the current `main` on October 14. We read the code; we did not run the extension on the sampled repositories.

- A direct `uses: docker://image:tag` step in your own workflow gets a warning: "is not covered by the actions lockfile; container image tags are mutable" ([`workflowfile.go#L79-L92`](https://github.com/github/gh-actions-lock/blob/d5dca22a06ff8590d50b41612038996800cfb336/internal/workflowfile/workflowfile.go#L79-L92)).
- A Docker container action reached through `uses: owner/repo@ref` gets no warning. Dependency discovery continues only into composite actions ([`discovery.go#L203`](https://github.com/github/gh-actions-lock/blob/d5dca22a06ff8590d50b41612038996800cfb336/internal/resolve/discovery.go#L203)), and the action metadata parser does not read `runs.image`.
- A `docker://` step inside a remote composite action is skipped without a warning ([`discovery.go#L247-L250`](https://github.com/github/gh-actions-lock/blob/d5dca22a06ff8590d50b41612038996800cfb336/internal/resolve/discovery.go#L247-L250)). `getsentry/action-release@v3` is one: its composite runs `docker://ghcr.io/getsentry/action-release-image:3.7.1`.

We asked for the warning to cover these cases, and for one sentence in the docs, in [github/gh-actions-lock#168](https://github.com/github/gh-actions-lock/issues/168).

## How common it is

1,978 repositories from GitHub search on October 14 (10 languages; 100 to 2,000 stars sorted by last update, and over 5,000 stars sorted by stars; pushed in the last 30 days; no forks or archives), 1,802 of them with workflows. For each remote action we read its `action.yml` at the referenced ref and followed composite steps.

| Repositories with workflows (1,802) | Count | Share |
|---|---|---|
| Use an action that pulls a prebuilt image by tag, no warning | 177 | 9.8% |
| Pull a prebuilt image by tag, or build a Docker action from a `FROM` not pinned by digest | 382 | 21.2% |
| Of those 382, reach the image through a `uses:` already pinned to a full SHA | 220 | |
| Have a direct `uses: docker://…:tag` step (the case that warns) | 21 | 1.2% |
| Cannot be locked at all: a remote composite calls `./…` | 111 | 6.2% |

The prebuilt images are concentrated in a few actions: `ossf/scorecard-action` (81 repositories), `EnricoMi/publish-unit-test-result-action` (21), `getsentry/action-release` (11) and GitHub's own `actions/jekyll-build-pages` (10). Of the 111 repositories that cannot be locked, 99 use `pypa/gh-action-pypi-publish`; that is [github/gh-actions-lock#128](https://github.com/github/gh-actions-lock/issues/128). Per-action counts are in `results/summary.txt`.

358 of the 4,383 action files we requested returned 404, so every count here is a lower bound.

## Check your own repository

`scripts/scan.py` reads `.github/workflows/` in a local checkout, fetches each remote action's `action.yml` (and, for a Docker action built at run time, its Dockerfile) from `raw.githubusercontent.com` without credentials, and runs nothing from the repository. It needs Python 3 and PyYAML. Download `scripts/scan.py`, then:

```bash
pip install pyyaml
python3 scan.py /path/to/your/repo
```

It prints one JSON line per repository. Each finding has a `kind`, the `via` that leads to it, and the `image`:

- `action-image-tag`: a Docker action whose image is a registry tag
- `composite-docker-tag`: a `docker://` step inside a remote composite action
- `action-dockerfile`: a Docker action built at run time; `base` lists `FROM` images not pinned by digest
- `workflow-docker-tag`: a `docker://` step in your own workflow (the extension already warns)
- `composite-local-path`: a remote composite calls `./…`, so the workflow cannot be locked
- `job-container-tag`: a job `container:` or `services:` image by tag (not an action dependency; shown for completeness)

An image counts as pinned when it ends in `@sha256:…`. Fetched files are cached in `action-cache.json` in the current directory.

## What to do

- Read a clean lockfile diff as "no action code changed", not "nothing that runs changed". For each `action-image-tag` or `composite-docker-tag` finding, the image is outside the lockfile.
- Ask the maintainers of those actions to reference their image by digest in `action.yml` (`image: docker://ghcr.io/org/image@sha256:…`). A digest in the action's own commit is covered by your lockfile, because the commit is.
- `action-dockerfile` actions are rebuilt on every run from their `FROM` images, so the result can change even when the action's commit does not.

## Method and limits

- Static read of workflow and action files at each repository's default branch on October 14. Runner behaviour is inferred from `action.yml` semantics; we did not run any workflow.
- The sample comes from search ranking, not random selection. Sampling and clone scripts are in `scripts/fetch_list.py` and `scripts/clone.sh`; `scripts/summarize.py` produces `results/summary.txt`. We do not publish the list of sampled repositories.
- Remote reusable workflows are not followed, because a reusable workflow is covered by its own repository's lockfile.
- Tools that `node` or composite actions download at run time (for example `setup-*` actions or `curl | sh` steps) are another gap; we did not measure them.

## Who did this

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. The agents built the sample, ran the scanner and read the `gh-actions-lock` source. Our scripts and text are MIT-licensed (`LICENSE`). Send corrections to [hello@cybernative.ai](mailto:hello@cybernative.ai); CyberNative AI LLC will publish dated public corrections in this note.
