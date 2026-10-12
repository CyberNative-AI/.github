# `ubuntu-latest` becomes Ubuntu 26.04: about 1 in 5 sampled Python and Ruby repos have a job that fails at setup

GitHub moves the `ubuntu-latest` label from Ubuntu 24.04 to 26.04 between October 19 and November 19, 2026 ([actions/runner-images#14748](https://github.com/actions/runner-images/issues/14748)). `actions/setup-python` and `ruby/setup-ruby` download a build made for the runner's exact Ubuntu version, and far fewer builds exist for 26.04. A job that asks for a missing version fails at its setup step:

```
The version '3.9' with architecture 'x64' was not found for ubuntu 26.04.
Unavailable version 3.4.4 for ruby on ubuntu-26.04
```

We checked 547 active public Python and Ruby repositories that set up Python or Ruby on `ubuntu-latest`. **117 (21%) have at least one job predicted to fail at setup on 26.04**: 75 of 224 Ruby repositories (33%) and 42 of 323 Python repositories (13%). In 115 of the 117, the failing job has no `continue-on-error`. We are not naming repositories; the checker below runs on your own.

## What installs on 26.04

As of October 12, 2026 (x64):

| | Versions with a 26.04 build |
|---|---|
| Python 3.8, 3.9 | none |
| Python 3.10 – 3.14 | 3.10.20–3.10.22, 3.11.15–3.11.17, 3.12.13–3.12.15, 3.13.13–3.13.16, 3.14.6–3.14.8 |
| Ruby before 3.2 | none |
| Ruby 3.2 – 4.0 | 3.2.11, 3.3.11–3.3.12, 3.4.9–3.4.11, 4.0.5–4.0.7 |

Sources: [python-versions `versions-manifest.json`](https://github.com/actions/python-versions/blob/main/versions-manifest.json) and the [ruby-builder releases](https://github.com/ruby/ruby-builder/releases). A minor-version request such as `'3.12'` or `'3.4'` resolves to one of these and keeps working.

The failing steps in the sample (after matrix expansion), by cause:

| Cause | Failing steps |
|---|---|
| Ruby 2.5–3.1 | 193 |
| Ruby exact patch release without a 26.04 build, often in `.ruby-version` (3.4.4, 3.4.8, 3.3.0, 4.0.1) | 181 |
| Python 3.8 or 3.9 | 61 |
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

Nothing is reported `OK` unless it was resolved. The exit status is 1 when any entry is `BREAK`; `--json` prints one object per repository.

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
- **Tests.** `python3 -m unittest discover -s tests` runs 17 fixture tests against the October 12 data in `tests/data/`. `python3 tests/mutants.py` checks that they catch 12 seeded faults.

## How the sample was drawn

GitHub repository search, anonymous, on October 12, 2026: not forks, not archived, pushed since September 12. Depth-1 sparse clones of the default branch (workflows and version files only). A repository counts when at least one setup-python or setup-ruby step runs on a hosted `ubuntu-latest` job.

| Search | Repos | With a setup step | ≥1 `BREAK` | Share |
|---|---|---|---|---|
| Python, 100–1,000 stars, most recently updated | 299 | 190 | 23 | 12.1% |
| Python, more than 5,000 stars | 200 | 133 | 19 | 14.3% |
| Ruby, 50–1,000 stars, most recently updated | 200 | 138 | 42 | 30.4% |
| Ruby, more than 1,000 stars | 100 | 86 | 33 | 38.4% |
| **All** | 799 | 547 | **117** | **21.4%** |

To draw a fresh sample the same way (search results change, so you will get a different list):

```sh
cd sample && python3 fetch_list.py && cd ..
grep -v '^#' sample/repos.tsv | cut -f2 | xargs -P 10 -n 1 sample/clone.sh repos
python3 check2604.py --json repos/*/ > sample/results.jsonl
python3 sample/summarize.py
```

`emulation/sp.sh` and `emulation/rr.sh` rerun the container check. They need Docker, a node 24 binary (`NODE=...`) and a checkout of the action at the commit above. Create `emulation/logs/` and `emulation/stubs/` first.

## Limits

- A prediction from workflow files, confirmed in containers, not on hosted runners. The tool-cache contents come from the runner image READMEs as of October 12.
- x64 runners labelled exactly `ubuntu-latest`. Not covered: arm64, self-hosted, Windows, macOS, and jobs that run in a `container:`.
- The sample is search-ranked, not random. "Most recently updated" favours very active repositories.
- `UNKNOWN` steps are not counted as failures. 96 of the 547 repositories have at least one (24 of them have a Ruby `head` build step), and 13 have nothing else. The share is a lower bound for what the files show.
- A break in a workflow that runs only on release or manual dispatch counts.
- python-versions and ruby-builder may publish more 26.04 builds after October 12.
- Other 26.04 changes (compiler, removed packages) are out of scope. PyPy and GraalPy builds are not tied to an Ubuntu version.

The code is MIT-licensed (`LICENSE`). Published by CyberNative AI LLC. AI-assisted research and writing; corrections: hello@cybernative.ai.
