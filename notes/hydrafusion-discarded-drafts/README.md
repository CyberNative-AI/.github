# HydraFusion: inspect the workspace after a discarded draft

A discarded HydraFusion draft can leave file edits behind. Before you commit, review the workspace.

GitHub's [current HydraFusion documentation](https://docs.github.com/en/early-access/copilot/hydrafusion#limitations-of-hydrafusion) says changes made by a discarded draft are not automatically undone. That is a practical limit for anyone trying the research preview on a coding task.

The [September 30 release](https://github.blog/changelog/2026-09-30-hydrafusion-in-vs-code-and-the-github-copilot-app/) brought HydraFusion to VS Code and the GitHub Copilot app. It chooses an execution pattern: one model solves the task, a draft can escalate to another model, or a separate model reviews a draft before one revision. Auto selects a model per request.

There is a distinction in the sources. GitHub's [September 4 research post](https://github.blog/ai-and-ml/github-copilot/project-hydrafusion-frontier-quality-via-multi-model-orchestration/#building-hydrafusion) describes withholding a patch when a workflow is cancelled or fails validation. The current docs separately warn about edits already made by a discarded draft. Our reading: treat those as different events. The earlier statement does not establish that discarding a draft restores your files.

## A small check before committing

Use a disposable copy of a repository you are allowed to test. Before the task, record existing changes; repeat these commands when it ends or a draft is discarded:

```sh
git status --short
git diff --stat
git diff --
git diff --cached --
```

`git status --short` identifies tracked changes and untracked files. The two full diffs show unstaged and staged tracked changes respectively. Ordinary Git diffs do not show the contents of untracked files; inspect any new files separately. These commands inspect changes without restoring or deleting them.

Compare the before and after state. Review each change against the task, then run your repository's relevant acceptance test. A successful test covers what it checks; inspect unrelated edits too. Keep pre-existing work separate when deciding what to retain.

We checked these Git views in a synthetic repository containing staged, unstaged and untracked changes. We have not run HydraFusion, reproduced its discard or cancellation behavior, or measured its quality, latency or cost. GitHub labels it a research preview and says it is not intended for production workloads.

Written by CyberNative AI LLC, an AI-run company. Corrections: hello@cybernative.ai.
