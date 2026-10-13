# `ubuntu-latest` becomes Ubuntu 26.04: setup-beam cannot install Erlang/OTP 24 or 25 there

GitHub moves the `ubuntu-latest` label from Ubuntu 24.04 to 26.04 between October 19 and November 19, 2026 ([actions/runner-images#14748](https://github.com/actions/runner-images/issues/14748)). `erlef/setup-beam` installs an Erlang/OTP build made for the runner's Ubuntu version, from builds.hex.pm. The 26.04 list starts at OTP 26.0, so a job that asks for OTP 24 or 25 fails at its setup step:

```
Requested loose Erlang/OTP version (25) not found in version list, at /builds/otp/amd64/ubuntu-26.04/builds.txt, with mirrors https://builds.hex.pm. Should you be using option 'version-type': 'strict'?
```

The hint at the end does not help: there is no strict OTP 24 or 25 version for 26.04 either.

A setup-beam pinned to v1.24.0 or earlier, including v1.24.0 from March 2026, fails on 26.04 whichever OTP version it asks for, because it does not know the 26.04 image:

```
Tried to map a target OS from env. variable 'ImageOS' (got ubuntu26), but failed.
```

We checked the GitHub repositories of the 500 hex.pm packages with the most recent downloads. 224 of them run setup-beam in an `ubuntu-latest` job. **89 of those 224 (40%) have at least one job that installs today on 24.04 and fails at setup on 26.04.** Among the 124 with a commit in the last 90 days, 43 (35%) do. None of the failing jobs is marked `continue-on-error`. We are not naming repositories; the checker below runs on your own.

## What installs on 26.04

builds.hex.pm, as of October 13, 2026 (amd64):

| OTP | Ubuntu 24.04 | Ubuntu 26.04 |
|---|---|---|
| 24 | 24.3.4 – 24.3.4.17 | none |
| 25 | 25.0 – 25.3.2.21 | none |
| 26 | 26.0 – 26.2.5.21 | 26.0 – 26.2.5.21 |
| 27 | 27.0 – 27.3.4.18 | 27.0 – 27.3.4.18 |
| 28 | 28.0 – 28.5.0.7 | 28.0 – 28.5.0.7 |
| 29 | 29.0 – 29.1.1 | 29.0 – 29.1.1 |

26.0 release candidates and the `maint-25`/`maint-26` branch builds exist only for 24.04.

Source: `https://builds.hex.pm/builds/otp/amd64/ubuntu-24.04/builds.txt` and `.../ubuntu-26.04/builds.txt`. Elixir, Gleam and rebar3 builds do not depend on the Ubuntu version and are not affected.

Of the 89 repositories, 83 have an OTP 24 or 25 entry, 7 have an old pinned setup-beam (2 have both), and 1 asks for OTP 26.0-rc1. The pinned refs were `v1.20.4`, `v1.18.2` and three commit SHAs: v1.24.0 (`fc68ffb`), v1.20.4 (`e6d7c94`) and an untagged commit from October 2025 (`566deeb`). `erlef/setup-beam@v1` currently points to v1.24.1 and is not affected.

## Fixes, per entry

- **Keep an OTP 24 or 25 entry on 24.04**, for as long as GitHub keeps the 24.04 image:
  ```yaml
  strategy:
    matrix:
      include:
        - otp: "25"
          elixir: "1.14"
          os: ubuntu-24.04
        - otp: "27"
          elixir: "1.18"
          os: ubuntu-latest
  runs-on: ${{ matrix.os }}
  steps:
    - uses: erlef/setup-beam@v1
      with:
        otp-version: ${{ matrix.otp }}
        elixir-version: ${{ matrix.elixir }}
  ```
- **Or raise the entry to OTP 26.0 or later**, a release rather than a 26.0 release candidate. That entry may also need a newer Elixir version.
- **Move a pinned setup-beam to v1.24.1** (`54075bcc5e249e4758d363f27d099f55d843f124`) or later.

Do not switch to `version-type: strict`: it changes how the version is matched, not which builds exist.

## Check your repository

The checker reads `.github/workflows/*.yml` and, for `version-file`, `.tool-versions` or `mise.toml`. It expands each job's matrix and resolves every setup-beam step with a port of the action's own version matching, for both the 24.04 and the 26.04 build list. It runs nothing from your repository, needs no token and no node.

```sh
curl -fsSLO https://raw.githubusercontent.com/CyberNative-AI/.github/main/notes/ubuntu-2604-setup-beam/checkbeam2604.py
uv run --no-project --with pyyaml checkbeam2604.py path/to/repo
# or, where PyYAML is installed (Python 3.11+): python3 checkbeam2604.py path/to/repo
```

On the synthetic repository in `example/` it prints this and exits with status 1:

```
BREAK    setup-beam    25         .github/workflows/ci.yml:test[otp=25,elixir=1.14,os=ubuntu-latest]: otp-version: 24.04->OTP-25.3.2.21 26.04->None
OK       setup-beam    27         .github/workflows/ci.yml:test[otp=27,elixir=1.17,os=ubuntu-latest]: otp-version: 24.04->OTP-27.3.4.18 26.04->OTP-27.3.4.18
OK       setup-beam    28         .github/workflows/ci.yml:test[otp=28,elixir=1.18,os=ubuntu-latest]: otp-version: 24.04->OTP-28.5.0.7 26.04->OTP-28.5.0.7
BREAK    setup-beam    27         .github/workflows/ci.yml:lint: erlef/setup-beam@v1.20.4 does not know the 26.04 image (v1.24.1 or later does)
OK       setup-beam    26.2.5.21  .github/workflows/ci.yml:release: .tool-versions: 24.04->OTP-26.2.5.21 26.04->OTP-26.2.5.21
```

The example's OTP 25 entry that already runs on `ubuntu-24.04` is not listed: only `ubuntu-latest` jobs are checked.

| Status | Meaning |
|---|---|
| `BREAK` | installs on 24.04 today; fails at setup on 26.04 (no OTP build, or a setup-beam older than v1.24.1) |
| `OK` | installs on 26.04 |
| `ALREADY` | fails on 24.04 too, for example OTP older than 24.3.4, or `version-file` without `version-type: strict` |
| `UNKNOWN` | cannot be resolved from the files: expressions from inputs, `needs` or `vars`, generated matrices, an `ImageOS` override, other setup actions, a setup-beam ref it cannot place |

- `--json` prints one object per repository. Exit status 1 means at least one `BREAK`.
- The first run downloads both builds.txt lists from builds.hex.pm into `data/` next to the script. To check again after builds.hex.pm adds 26.04 builds, pass `--refresh`.
- Pinned setup-beam refs: every release tag and its commit is built in, so `@v1.20.4` or a tagged SHA is placed offline. Any other ref, such as an untagged SHA or a branch, is looked up once, anonymously, from `raw.githubusercontent.com/erlef/setup-beam/<ref>/dist/index.js` (about 0.9 MB) and cached in `data/`. If that fails, or with `--offline`, the step is `UNKNOWN`.

## How the prediction was checked

- **Against the action itself.** We ran setup-beam's released `dist/index.js` under node 24.21.0 in `ubuntu:26.04` and `ubuntu:24.04` containers, with the runner's `ImageOS` value and an empty tool cache. On 26.04, v1.24.1 with OTP 25 and v1.24.0 (`fc68ffb`, March 30, 2026) with OTP 27 both failed with the errors above. v1.24.1 with OTP 25 on 24.04, v1.24.0 with OTP 27 on 24.04, and v1.24.1 with OTP 27 on 26.04 installed, and `erl` ran.
- **Version matching.** The checker is a Python port of setup-beam v1.24.1's version matching and the node-semver 7.7.4 functions it calls. On the October 13 build lists it gives the same answer as the action's own code in all 15,592 cases: 3,898 `otp-version` values, loose and strict, on 24.04 and 26.04. They include every value in the sample, 17 hand-written ones (release candidates, `latest`, branches, ranges, `OTP-` prefixes), every build in both lists and 1,500 random combinations. `python3 tests/parity/compare.py` checks this; `tests/parity/oracle.mjs` regenerates the expected answers from a setup-beam v1.24.1 checkout (needs node, see its header).
- **Tests.** `python3 -m unittest discover -s tests` runs 34 fixture tests against the October 13 lists in `tests/data/`, with no network. `python3 tests/mutants.py` checks that the tests and the parity check catch 16 seeded faults.
- **Rerun the container checks** with `e2e/run.sh` (Docker, a node 24 binary and checkouts of setup-beam v1.24.1 and v1.24.0; its header shows how to get them).
- One approximation: for an old pinned setup-beam, the checker still uses v1.24.1's version matching. That only affects whether the step installs on 24.04 today; on 26.04 an old pin fails before any matching.

## How the sample was drawn

hex.pm API, October 13, 2026: the 500 packages with the most recent downloads, mapped to 484 GitHub repositories (481 cloned, default branch). A repository counts when at least one setup-beam step runs in a hosted `ubuntu-latest` job without a `container:`.

| Repositories | With a setup-beam step on `ubuntu-latest` | ≥1 job fails at setup on 26.04 | Share |
|---|---|---|---|
| All | 224 | 89 | 39.7% (95% interval 34–46%) |
| Commit in the last 365 days | 180 | 65 | 36.1% |
| Commit in the last 90 days | 124 | 43 | 34.7% |

In 78 of the 89, a workflow with nothing failing today would turn red. Counting every step we could not resolve as a failure gives 100 of 224 (45%).

To draw the sample again (download counts change, so the list may differ):

```sh
cd sample && python3 fetch_list.py && cd ..
grep -v '^#' sample/repos.tsv | cut -f2 | sort -u | xargs -P 10 -n 1 sample/clone.sh repos
for d in repos/*/; do echo "$(basename "$d") $(cat "$d/.head-date")"; done > sample/head-dates.txt
python3 checkbeam2604.py --json repos/*/ > sample/results.jsonl
python3 sample/summarize.py sample/results.jsonl sample/head-dates.txt
```

`clone.sh` makes a depth-1 sparse clone of each default branch with only `.github/workflows/`, `.tool-versions` and `mise.toml`. To count against the October 13 build lists rather than today's, run `mkdir -p data && cp tests/data/*.txt data/` before the checker step.

## Limits

- A prediction from workflow files, confirmed in containers, not on hosted runners.
- x64 runners labelled exactly `ubuntu-latest`. Not covered: arm64, self-hosted, Windows, macOS, jobs in a `container:` or with `ImageOS` overridden, and workflows on other branches.
- `UNKNOWN` steps (versions from inputs, `vars`, `needs` or generated matrices) are not counted as failures, so the share is a lower bound for what the files show.
- The frame is the most-downloaded libraries, not a random sample of Elixir and Erlang projects.
- builds.hex.pm may publish more 26.04 builds after October 13.

The code is MIT-licensed (`LICENSE`). Published by CyberNative AI LLC. AI-assisted research and writing; corrections: hello@cybernative.ai.
