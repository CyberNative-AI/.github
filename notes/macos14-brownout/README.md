# Before the macOS 14 brownout: find the labels, then check the architecture

GitHub's first scheduled macOS 14 brownout runs **October 5, 2026, 14:00 UTC to October 6, 00:00 UTC**. Jobs using `macos-14`, `macos-14-large` or `macos-14-xlarge` will temporarily fail. Retirement is November 2. These dates come from [GitHub's October 1 notice](https://github.blog/changelog/2026-10-01-github-actions-macos-14-runner-image-retirement/); check it for the remaining windows.

For maintainers of macOS CI, the useful first step is a search of the workflow files. Run this from your repository root with [ripgrep](https://github.com/BurntSushi/ripgrep) installed:

```sh
rg -n --hidden --glob '*.yml' --glob '*.yaml' \
  '\bmacos-14(-large|-xlarge)?\b' .github/workflows
```

Read every candidate, including matrix entries. A text match can be a comment or an expected-output fixture. No matches means only that this search found no literal old label within its search scope. Ignore rules still apply; expressions, generated workflows and externally hosted reusable workflows need their own inspection. ripgrep exits 1 when it finds no matches; an error has a different meaning.

## Choose the replacement by architecture

GitHub's [current runner image list](https://github.com/actions/runner-images#available-images) identifies `macos-15` as arm64 and `macos-15-intel` as x64. It also distinguishes `macos-15-large` (x64) from `macos-15-xlarge` (arm64). The suffix is part of the runner choice, not a detail to remove during a bulk replacement. Larger-runner access and billing differ from standard runners; do not switch classes casually.

Choose the supported label that fits your existing build and account, then check the actual job log. On the selected macOS runner, these commands help expose the machine and Xcode environment:

```sh
uname -m
sw_vers -productVersion
xcodebuild -version
```

Run your project's build and tests on that runner. [GitHub documents](https://docs.github.com/en/actions/reference/runners/github-hosted-runners#limitations-for-arm64-macos-runners) arm64 limits affecting community actions, nested virtualization and signing workflows that require a static UDID. A label search cannot establish compatibility with those requirements.

## A real workflow search, before and after

Astral's [setup-uv change](https://github.com/astral-sh/setup-uv/pull/1081), merged October 2, replaces macOS 14 in two test matrices and removes an old cache-key case already covered by macOS 15. We ran the command above against the changed `test.yml` at its pinned base and merged revisions: **four matching lines before; no matches after**. One match was an expected-output string. That is a workflow-text result, not an independent execution of setup-uv's CI.

Rerun that narrow comparison with [reproduce.sh](reproduce.sh):

```sh
bash reproduce.sh ./macos14-search-example
```

The script downloads one public workflow at each pinned revision into the directory you supply. It does not run the workflow, edit your repository or choose a replacement. It requires Bash, curl and ripgrep; network or search errors stop the comparison. The downloaded files remain available for inspection.

**Scope:** sources and workflow text checked October 4, 2026. No macOS job, build, signing task or brownout behavior was executed for this note. Use the source notice for the schedule and your actual CI run for migration acceptance.

Published by CyberNative AI LLC. AI-assisted writing and local source check; corrections: hello@cybernative.ai.
