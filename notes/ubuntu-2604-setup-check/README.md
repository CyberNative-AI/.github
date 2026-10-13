# `ubuntu-latest` becomes Ubuntu 26.04: about 1 in 5 sampled Python and Ruby repos have a job that fails at setup

GitHub moves the `ubuntu-latest` label from Ubuntu 24.04 to 26.04 between October 19 and November 19, 2026 ([actions/runner-images#14748](https://github.com/actions/runner-images/issues/14748)). `actions/setup-python` and `ruby/setup-ruby` download a build made for the runner's exact Ubuntu version, and far fewer builds exist for 26.04. A job that asks for a missing version fails at its setup step:

```
The version '3.9' with architecture 'x64' was not found for ubuntu 26.04.
Unavailable version 3.4.4 for ruby on ubuntu-26.04
```

We checked 548 active public Python and Ruby repositories that set up Python or Ruby on `ubuntu-latest`. **122 (22%) have at least one job predicted to fail at setup on 26.04**: 79 of 224 Ruby repositories (35%) and 43 of 324 Python repositories (13%). In 120 of the 122, the failing job has no `continue-on-error`. We are not naming repositories; the checker below runs on your own.

*Updated October 13, 2026:* the checker now resolves fallbacks such as `runs-on: ${{ matrix.os || 'ubuntu-latest' }}`, and `include` entries expand as GitHub documents: an entry no longer merges into a job that an earlier entry added, which had collapsed include-only matrices into one job. On the same October 12 sample and data, the count rose from 117 of 547 (21%) to 122 of 548. No repository lost a predicted failure. If you ran the checker before, download it again.

## What installs on 26.04

As of October 12, 2026 (x64):

| | Versions with a 26.04 build |
|---|---|
| Python 3.8, 3.9 | none |
| Python 3.10 – 3.15 | 3.10.20–3.10.22, 3.11.15–3.11.17, 3.12.13–3.12.15, 3.13.13–3.13.16, 3.14.6–3.14.8, 3.15.0 |
| Ruby before 3.2 | none |
| Ruby 3.2 – 4.0 | 3.2.11, 3.3.11–3.3.12, 3.4.9–3.4.11, 4.0.5–4.0.7 |

Sources: [python-versions `versions-manifest.json`](https://github.com/actions/python-versions/blob/main/versions-manifest.json) and the [ruby-builder releases](https://github.com/ruby/ruby-builder/releases). A minor-version request such as `'3.12'` or `'3.4'` resolves to one of these and keeps working.

The failing steps in the sample (after matrix expansion), by cause:

| Cause | Failing steps |
|---|---|
| Ruby 2.3–3.1 | 200 |
| Ruby exact patch release without a 26.04 build, often in `.ruby-version` (3.4.4, 3.4.8, 3.3.0, 4.0.1) | 193 |
| Python 3.8 or 3.9 | 74 |
| Python exact patch release without a 26.04 build | 21 |

## Check your repository

The checker reads `.github/workflows/*.yml` and the version files the actions read (`.python-version`, `pyproject.toml`, `.tool-versions`, `Pipfile`, `.ruby-version`, `mise.toml`). It expands each job's matrix and resolves every setup step the way the action does, for both the 24.04 and the 26.04 image. It runs nothing from your repository and needs no token.

```sh
curl -fsSLO https://raw.githubusercontent.com/CyberNative-AI/.github/main/notes/ubuntu-2604-setup-check/check2604.py
uv run --no-project --with pyyaml check2604.py path/to/repo
# or, where PyYAML is installed (Python 3.11+): python3 check2604.py path/to/repo
```

```
BREAK    setup-python  3.9        .github/workflows/ci.yml:test[python-version=3.9]: python-version: 24.04->3.9.25 26.04->None
OK       setup-python  3.12       .github/workflows/ci.yml:test[python-version=3.12]: python-version: 24.04->3.12.15 26.04->3.12.14
BREAK    setup-python  3.13.2     .github/workflows/ci.yml:test[python-version=3.13.2]: python-version: 24.04->3.13.2 26.04->None
BREAK    setup-ruby    3.4.4      .github/workflows/ci.yml:rb: version file: ruby-3.4.4 24.04 HTTP 200, 26.04 HTTP 404
```

| Status | Meaning |
|---|---|
| `BREAK` | installs on 24.04 today; no build on 26.04 |
| `OK` | installs on 26.04 |
| `ALREADY` | fails on 24.04 too, for example an unquoted `3.10`, which YAML reads as 3.1 |
| `UNKNOWN` | cannot be resolved from the files: expressions from inputs, `needs` or `vars`, generated matrices, `head` builds |

A `||` fallback such as `${{ matrix.os || 'ubuntu-latest' }}` is resolved the way the runner does it: a matrix value the entry does not set counts as empty. Nothing is reported `OK` unless it was resolved. The exit status is 1 when any entry is `BREAK`; `--json` prints one object per repository.

The first run downloads the python-versions manifest and setup-ruby's version list into `data/` next to the script, and checks ruby-builder assets with HEAD requests. Both projects can add 26.04 builds during the rollout: delete `data/` before you check again.

## Fixes, per entry

- **Keep that entry on 24.04** for as long as GitHub keeps the 24.04 image:
  ```yaml
  strategy:
    matrix:
      ruby: ["3.2", "3.3", "3.4"]
      os: [ubuntu-latest]
      include:
        - ruby: "3.1"
          os: ubuntu-24.04
  runs-on: ${{ matrix.os }}
  ```
- **Request a minor version** (`'3.12'`, `'3.4'`), or move an exact pin, including the one in `.ruby-version` or `.python-version`, to a release in the table above.
- **Python 3.8 or 3.9 on 26.04 itself:** uv's portable builds. With uv 0.13.0, `uv python install 3.9` and `uv venv --python 3.9` worked in a bare `ubuntu:26.04` container for 3.8.20 and 3.9.25; pytest and numpy from wheels passed on each. We have no tested route for Ruby before 3.2 on 26.04.

## How the prediction was checked

- **Against the actions themselves.** We took 22 real entries from the sample and ran the released actions in `ubuntu:26.04` and `ubuntu:24.04` containers, with a hosted runner's action environment and an empty tool cache. We used setup-python at `3892123f` and setup-ruby at `651ff0d6`, under node 24.21.0. All 22 matched the prediction. The 9 predicted `BREAK` failed on 26.04 with the action's own error, and the 4 of them we ran on 24.04 installed. The 9 predicted `OK` installed on 26.04. See `emulation/agreement.tsv`.
- **Version ranges.** The range matching agrees with node-semver (npm's bundled copy in `node:24`) on 10,496 version/range pairs: `python3 tests/semver_compare.py`.
- **Tests.** `python3 -m unittest discover -s tests` runs 19 fixture tests against the October 12 data in `tests/data/`. `python3 tests/mutants.py` checks that they catch 15 seeded faults.

## How the sample was drawn

GitHub repository search, anonymous, on October 12, 2026: not forks, not archived, pushed since September 12. Depth-1 sparse clones of the default branch (workflows and version files only). A repository counts when at least one setup-python or setup-ruby step runs on a hosted `ubuntu-latest` job.

| Search | Repos | With a setup step | ≥1 `BREAK` | Share |
|---|---|---|---|---|
| Python, 100–1,000 stars, most recently updated | 299 | 190 | 24 | 12.6% |
| Python, more than 5,000 stars | 200 | 134 | 19 | 14.2% |
| Ruby, 50–1,000 stars, most recently updated | 200 | 138 | 44 | 31.9% |
| Ruby, more than 1,000 stars | 100 | 86 | 35 | 40.7% |
| **All** | 799 | 548 | **122** | **22.3%** |

To draw a fresh sample the same way (search results change, so you will get a different list):

```sh
cd sample && python3 fetch_list.py && cd ..
grep -v '^#' sample/repos.tsv | cut -f2 | xargs -P 10 -n 1 sample/clone.sh repos
python3 check2604.py --json repos/*/ > sample/results.jsonl
python3 sample/summarize.py
```

`emulation/sp.sh` and `emulation/rr.sh` rerun the container check. They need Docker, a node 24 binary (`NODE=...`) and a checkout of the action at the commit above. Create `emulation/logs/` and `emulation/stubs/` first.

## Coreutils: Rust rewrite and measured command differences

In our tested Ubuntu 26.04 container, `base64`, `cut`, `date`, `nproc` and the other tested coreutils are [uutils coreutils](https://github.com/uutils/coreutils) 0.10.0, a Rust rewrite, instead of GNU coreutils 9.4. We extracted 5,133 direct coreutils calls from bash `run:` steps in 602 of 1,297 repositories selected through GitHub searches (stars ≥10, pushed September 21–October 11, 2026; one repository per owner). Each distinct call ran against synthetic files under GNU 9.4, uutils 0.10.0 and GNU 9.7. The frozen analysis ruled the run INVALID because its determinism gate failed. In a post-hoc analysis, we tested representative realistic inputs for the commands that differed, then applied one label per command to all its confirmed divergent occurrences. That assigned no breaking labels among the 1,297 repositories under `C.UTF-8` and the assumption of no CPU quota. We did not run complete workflows or test every occurrence with its real inputs.

What does behave differently:

| Call in the sample | Repos | 24.04 (GNU 9.4) | 26.04 (uutils 0.10.0) |
|---|---|---|---|
| `echo "$SECRET" \| base64 -d > file`, secret without `=` padding | 32 | exit 1 | decodes |
| same, secret wrapped with Windows line endings (CRLF) | | exit 1 | decodes |
| same, invalid input such as a trailing space or an extra `=` | | exit 1, writes the decoded bytes | exit 1, writes nothing |
| `make -j$(nproc)` in a container with a CPU limit | 8 | the CPU affinity count | the quota-limited count |
| `cut -c` on non-ASCII text | 9 (all shorten a commit SHA, so identical) | counts bytes | counts characters |

Repos counts the sampled repositories with that call. Single-line and wrapped secrets decode identically, and 20 real `date -d` strings gave identical output in all 3 formats tried. The invalid-input row matters only where the failure is ignored (`|| true`, or a pipe without `pipefail`): the file used to hold the right bytes and is now empty. Without a CPU limit, both `nproc`s print the same number.

Two additional differences outside the inputs exercised by our fixture: `sha256sum -c` accepts a checksum line with leading spaces on 24.04 and rejects it on 26.04 (exit 1), and `timeout -s KILL` exits 137 on 24.04 but 124 on 26.04. Both are fixed upstream ([#15167](https://github.com/uutils/coreutils/pull/15167), [#15075](https://github.com/uutils/coreutils/pull/15075)) but not in a release yet; the latest is 0.12.0, and 26.04 ships 0.10.0.

Most of this is GNU's own change since 9.4, which dates from August 2023: GNU coreutils decodes unpadded base64 since 9.5, `nproc` honours cgroup v2 CPU quotas since 9.8, and `cut -c` counts characters since 9.11 ([NEWS](https://github.com/coreutils/coreutils/blob/master/NEWS)).

To see it yourself:

```sh
docker run --rm ubuntu:24.04 sh -c 'printf "aGVsbG8\n" | base64 -d; echo " exit $?"'   # base64: invalid input / hello exit 1
docker run --rm ubuntu:26.04 sh -c 'printf "aGVsbG8\n" | base64 -d; echo " exit $?"'   # hello exit 0
docker run --rm --cpus 2 ubuntu:24.04 nproc   # the CPU affinity count
docker run --rm --cpus 2 ubuntu:26.04 nproc   # 2
docker run --rm ubuntu:26.04 sh -c 'echo hi > f; sha256sum f | sed "s/^/  /" > s; sha256sum -c s; echo "exit $?"'   # exit 1 (24.04: f: OK, exit 0)
```

How this was measured: each distinct call ran in `ubuntu:24.04` and `ubuntu:26.04` containers (network off) against a synthetic file set, with GNU 9.7 from the 26.04 archive as a third arm. The 26.04 container has the same coreutils meta-package version listed in the [runner image README](https://github.com/actions/runner-images/blob/2c421200c9e6873283a7b1d63bb122bc906139a1/images/ubuntu/Ubuntu2604-Readme.md). We did not verify the hosted runner's installed uutils binary version. Code, call list, raw outputs and the commands to run it again: [`coreutils/`](coreutils/).

Limits: direct calls in `run:` steps only, not composite actions, called script files or `xargs`/`find -exec` children; `container:` jobs and non-bash shells excluded. Containers, not a hosted runner. Only uutils 0.10.0 was tested. We do not know whether hosted runners set a CPU limit. All runs used the runner's default `C.UTF-8` locale. With a real `en_US.UTF-8` locale, `sort`/`ls` ordering, `fold`, `numfmt --grouping` and `date %c` differ. Three sampled repositories set a non-default locale and call coreutils; those settings were not traced to individual steps. The default-locale result does not establish their behavior. Only 75.14% of extracted occurrences were exercised by the primary fixture.

## Limits

- A prediction from workflow files, confirmed in containers, not on hosted runners. The tool-cache contents come from the runner image READMEs as of October 12.
- x64 runners labelled exactly `ubuntu-latest`. Not covered: arm64, self-hosted, Windows, macOS, and jobs that run in a `container:`.
- The sample is search-ranked, not random. "Most recently updated" favours very active repositories.
- `UNKNOWN` steps are not counted as failures. 94 of the 548 repositories have at least one (25 of them have a Ruby `head` build step), and 11 have nothing else. The share is a lower bound for what the files show.
- A break in a workflow that runs only on release or manual dispatch counts.
- python-versions and ruby-builder may publish more 26.04 builds after October 12.
- Other 26.04 changes (compiler, removed packages) are out of scope; coreutils are covered in the section above. PyPy and GraalPy builds are not tied to an Ubuntu version.

The code is MIT-licensed (`LICENSE`). Published by CyberNative AI LLC. AI-assisted research and writing; corrections: hello@cybernative.ai.
