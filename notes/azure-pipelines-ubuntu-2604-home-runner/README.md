# Azure Pipelines on Ubuntu 26.04: `/home/vsts` is now `/home/runner` (tested October 23)

Microsoft is moving the `ubuntu-latest` image to Ubuntu 26.04 between October 19 and November
19, 2026 ([actions/runner-images#14748](https://github.com/actions/runner-images/issues/14748)).
On Microsoft-hosted Azure Pipelines agents running 26.04, the agent user is `runner`, not
`vsts`. The home directory and the whole pipeline workspace move with it:

| | Ubuntu 22.04 / 24.04 | Ubuntu 26.04 |
|---|---|---|
| Home | `/home/vsts` | `/home/runner` |
| Sources (`Build.SourcesDirectory`) | `/home/vsts/work/1/s` | `/home/runner/work/1/s` |

The 26.04 image readme, the `ubuntu-latest` announcement and the Azure Pipelines docs do not
mention it. The one public report we found is a user issue from October 22
([actions/runner-images#15028](https://github.com/actions/runner-images/issues/15028)).
GitHub Actions is not affected: its runners already used `/home/runner`.

In our new container layout, `/home/vsts` does not exist and the unprivileged user cannot
create it under root-owned `/home`. This models the effect of the home-directory change;
we did not inspect the complete filesystem of a hosted 26.04 agent. A pipeline that relies
on the old path can fail, or quietly do less than before, when its `ubuntu-latest` job lands
on 26.04. A pipeline with no `pool` or `vmImage` at all also gets `ubuntu-latest`
([Azure docs](https://learn.microsoft.com/azure/devops/pipelines/agents/hosted)).

## Is it already happening?

Yes, for jobs that ask for 26.04. In pythonocc-core's public
[build 6812](https://dev.azure.com/tpaviot/pythonocc-core/_build/results?buildId=6812), job
`Ubuntu_26_04_python314` checked out under `/home/runner/work/1/s`, while job
`Ubuntu_24_04_python311` checked out under `/home/vsts/work/1/s`.

The `ubuntu-latest` switch had not reached MNE-Python's Linux jobs in
[build 40474](https://dev.azure.com/mne-tools/mne-python/_build/results?buildId=40474), which
finished on October 23: those jobs still ran on Ubuntu 24.04. This observation does not
establish the rollout state of other projects.

## Check yours

In each repository with Azure Pipelines YAML:

```sh
git grep -n '/home/vsts'
```

A hit matters if its job runs on `ubuntu-latest`, on `ubuntu-26.04`, or on no image at all.
Jobs pinned to `ubuntu-24.04` or `ubuntu-22.04`, self-hosted pools, and lines that run inside a
container are not affected now. Pinned jobs will be when you move them or the image retires.
`git grep` does not see classic (UI-defined) pipelines, variable groups, or task groups; check
those in Azure DevOps.

To find out before Microsoft switches you, add a job with `vmImage: ubuntu-26.04`, or run a
branch with `ubuntu-latest` changed to `ubuntu-26.04`.

## What a hard-coded `/home/vsts` does in the new layout

We ran each line shape as the agent user in two container layouts, the old one (home
`/home/vsts`) and a new one modelled on 26.04 (home `/home/runner`, no `/home/vsts`). Every shape worked in the
old layout.

| Line in your pipeline | In the new container layout |
|---|---|
| `cd /home/vsts/work/1/s` | fails: No such file or directory |
| `ls`, read or `>` redirect into `/home/vsts/work/...` | fails: No such file or directory |
| `/home/vsts/.local/bin/tool` (direct call) | fails: No such file or directory |
| `mkdir -p /home/vsts/...` (without `sudo`) | fails: Permission denied |
| `UV_CACHE_DIR=/home/vsts/...`, then `uv venv` / `uv pip install` | fails, exit 2: Failed to initialize cache |
| `npm_config_cache=/home/vsts/...`, then `npm install` of a package tarball | fails, exit 243: EACCES |
| `PIP_CACHE_DIR=/home/vsts/...`, then `pip install` | works with a warning: pip disables its cache |
| `export PATH=/home/vsts/.local/bin:$PATH` | harmless: the image's `PATH` already includes `$HOME/.local/bin` |

Whether a failing line fails the job depends on the step. Under `set -e`, or when it is the
last command of a script step, the step fails. Otherwise the script runs on without the file,
folder or install it expected, and a later step may fail or produce less output.

## Fix

Replace the literal path with a value that is right in every layout:

| Instead of | In a script | In a YAML field (`variables:`, task inputs such as `Cache@2` `path:`) |
|---|---|---|
| `/home/vsts/work/1/s` | `$BUILD_SOURCESDIRECTORY` | `$(Build.SourcesDirectory)` |
| `/home/vsts/work/1` | `$PIPELINE_WORKSPACE` | `$(Pipeline.Workspace)` |
| `/home/vsts/work/1/a` | `$BUILD_ARTIFACTSTAGINGDIRECTORY` | `$(Build.ArtifactStagingDirectory)` |
| `/home/vsts/work/_temp` | `$AGENT_TEMPDIRECTORY` | `$(Agent.TempDirectory)` |
| any other `/home/vsts/...` | `$HOME/...` | a path under `$(Pipeline.Workspace)` or `$(Agent.TempDirectory)` |

The variables on the right are Azure Pipelines'
[predefined variables](https://learn.microsoft.com/azure/devops/pipelines/build/variables).
`HOME` is an environment variable, not one of these, so use the predefined variables in YAML
fields; we did not test `$(HOME)` there. We tested `$HOME` rewrites for `cd`, direct tool calls, `mkdir`, pip, uv and both npm
install shapes in scripts; those tests passed in both layouts.

If you cannot fix it now, pin the affected jobs to `vmImage: ubuntu-24.04` and fix it before you
unpin.

## How many public pipelines this hits

We collected 983 files in 767 public repositories from GitHub code searches for `/home/vsts`
on October 23. We treated 43 repositories as active: they were not archived, their
default-branch HEAD commit was dated April 23 or later, and that commit had an Azure
Pipelines check or an Azure DevOps status link. By reading their YAML, we classified 20 of
those 43 repositories (12 owners) as at risk when their exposed jobs move to 26.04. Fifteen
match command shapes tested in our containers; five depend on task or tool behavior we did
not execute. These are predictions from source inspection and container tests, not 20
observed hosted-agent failures. Nine of the 20 belong to one owner. This search does not
cover private repositories or classic pipelines, so the count is not a population estimate.

## What we did not test

- **Third-party tasks and tools** given a `/home/vsts` folder (for example an install path or a
  cache folder). We expect the Permission denied above, but did not run them.
- **`docker run -v /home/vsts/...:...`.** Docker creates a missing bind-mount source, so we
  expect an empty mount rather than an error. Not run.
- **`Cache@2` / `Cache@1` with a `path:` under `/home/vsts`.** Tools that write to their default
  folders under `$HOME` now write under `/home/runner`, so such an entry no longer matches what
  they write. Not run.
- **Task inputs that point at `/home/vsts`**, such as a `CopyFiles` source folder. These may
  find nothing instead of failing. Not run.
- **An actual hosted 26.04 agent.** We read the layout from public build logs and reproduced the
  effect of each line in containers; we did not run your pipeline. The container results are
  ours alone; nobody outside our company has reproduced them yet.

## Reproduce

[`reproduce/`](reproduce/) has the script that runs every shape in both layouts with Docker,
and its output from October 23.

More dated breaking changes across languages and platforms, with a weekly email:
[Breakage Calendar](https://cybernative.ai/breakage-calendar/?ref=note-azure2604). For the
GitHub Actions side of the same image change, see
[`ubuntu-latest` becomes Ubuntu 26.04: setup failures](../ubuntu-2604-setup-check/).

---

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai. We will record dated corrections on this page.
