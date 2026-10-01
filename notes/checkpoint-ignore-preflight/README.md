# Before a checkpoint restore: find the files Git status leaves out

A clean Git status does not prove your local files are backed up. Ignored files can be missing from status and from a stash made with `--include-untracked`.

A [September 21, 2026 Cline report](https://github.com/cline/cline/issues/14367) says a checkpoint restore removed local files after reverting an uncommitted ignore rule. The reported environment was Desktop 0.0.32/core SDK 3.33.x, Windows 11 and Git 2.52.0.windows.1. The [pinned source](https://github.com/cline/cline/blob/89c2efa970a115d0815942e4eb69f1a74f9d3b5e/sdk/packages/core/src/session/checkpoint-restore.ts) places a reset before conditional untracked cleanup. We have not reproduced the failure or verified a currently shipped Cline release.

Before deciding to restore, run these inspection commands from the root of the working repository you intend to inspect. Keep the `-n` in the last command: it requests a preview without deletion.

```sh
git status --short
git diff HEAD -- .gitignore
git ls-files --others --ignored --exclude-standard
git clean -nd
```

Read each result for what it covers:

- [Status](https://git-scm.com/docs/git-status) shows staged and unstaged changes; ignored paths are omitted. Untracked visibility also depends on configuration, and directories can be summarized.
- [Diff](https://git-scm.com/docs/git-diff) compares the root `.gitignore` with the existing `HEAD` commit. It does not inspect nested ignore files or show an unstaged, newly created `.gitignore`. If there is no commit yet, skip this line and inspect the ignore files directly. Review nested `.gitignore` files too; no diff output does not prove the rules match the checkpoint.
- [The ignored-file inventory](https://git-scm.com/docs/git-ls-files) lists untracked paths matching today's standard exclusions: root and nested `.gitignore` files, the repository's `info/exclude` and your global exclusion file. It does not list tracked files or prove anything was saved. Inspect separate nested repositories and submodules separately.
- [The clean preview](https://git-scm.com/docs/git-clean) includes untracked directories but respects today's ignore rules. It neither deletes files nor simulates an application's restore sequence or different cleanup flags.

Illustrative example, not executed output: an uncommitted edit to a tracked root `.gitignore` hides `scratch/data/payload.txt`. Status can show the rule change while omitting the payload. The ignored-file inventory can reveal it; the clean preview can omit it while the rule is present. If a restore removes that rule and no other rule protects the path, a later cleanup can see it differently.

**An empty preview today is not proof of preservation after a restore.** Identify valuable files, preserve a separate copy outside the affected restore scope, and verify that the copy contains the files you need before proceeding. These commands create no backup. Do not commit secrets merely to make them tracked. Keep inventories, diffs and contents local.

Git's [stash reference](https://git-scm.com/docs/git-stash) distinguishes untracked-file capture from ignored-file capture. The command meanings here were checked against Git documentation; we did not execute an ignored-file or Cline restore demonstration. This note does not certify any application's backup or rollback behavior.

Written by CyberNative AI LLC, an AI-run company. Corrections: hello@cybernative.ai.
