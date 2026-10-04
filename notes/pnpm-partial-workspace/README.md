# pnpm 11.28.4 accepts an omitted workspace — check the lockfile diff

If your build context leaves out a workspace directory, a successful frozen install can still change the lockfile. Check the exit status **and** the diff before treating the result as unchanged.

[pnpm 11.28.4](https://github.com/pnpm/pnpm/releases/tag/v11.28.4), released on 3 October 2026, restores frozen installs when a lockfile-listed project's directory is absent. A directory that exists without its `package.json` still fails. [The fix](https://github.com/pnpm/pnpm/pull/16462) describes that boundary; [the pinned v11 source](https://github.com/pnpm/pnpm/blob/5dafb0980042af99fb1aa24478d16f03b8474b50/pnpm11/installing/deps-installer/src/install/verifyFrozenLockfile.ts#L119-L142) checks directory existence before looking for a manifest.

We compared official Linux x64 releases 11.28.3 and 11.28.4 using one root project and two dependency-free members, `server` and `tests`. Each run starts from the same lockfile and uses `install --offline --frozen-lockfile --ignore-scripts`:

- Both complete workspaces succeed; the lockfile stays byte-identical.
- With `tests/` wholly absent, 11.28.3 exits 1 with `ERR_PNPM_OUTDATED_LOCKFILE`; 11.28.4 exits 0. Neither recreates the directory.
- With `tests/` present but its manifest missing, both exit 1. Adding a dependency to `server/package.json` without changing the lockfile also fails in both.
- **The successful 11.28.4 omitted-directory run removes `tests: {}` from `importers`.** The other seven runs leave the lockfile unchanged. [Recorded rows](results.json) and the [resulting lockfile](lock-after-omission.yaml) retain the evidence.

That last observation is specific to this fixture. It does not establish what happens to every lockfile or explain every CI failure. An absent directory can represent deliberate exclusion or accidental deletion; an exit code cannot tell you which.

## Reproduce the boundary

[Download the recipe ZIP](https://github.com/CyberNative-AI/.github/raw/refs/heads/main/notes/pnpm-partial-workspace/pnpm-partial-workspace.zip) and extract it. The ZIP contains synthetic inputs, this note, the standard-library runner and recorded results; it includes no pnpm binaries.

Use Python 3.10+ and absolute paths to the executables from the official [11.28.3](https://github.com/pnpm/pnpm/releases/tag/v11.28.3) and [11.28.4](https://github.com/pnpm/pnpm/releases/tag/v11.28.4) Linux x64 archives. Keep each executable beside its extracted `dist/` directory. Run from the extracted recipe directory. Set the two paths first; `boundary-run` must not exist:

```sh
PNPM_OLD=/absolute/path/to/11.28.3/pnpm
PNPM_NEW=/absolute/path/to/11.28.4/pnpm
python3 verify.py --old "$PNPM_OLD" --new "$PNPM_NEW" --output boundary-run
```

The runner checks executable versions, makes eight fresh workspace copies, disables lifecycle scripts and uses its own store/config/cache directories. It writes local `command.log` files and `boundary-run/results.json`. Expected: eight PASS lines; only the 11.28.4 absent-directory line says `lock unchanged=False`. It neither downloads nor installs pnpm. No registry dependencies are declared in the shipped workspace; the changed-manifest control fails before resolving its synthetic dependency.

## Limits

Tested on Linux x86_64 with the official archive hashes matched to GitHub's release metadata. This is filesystem omission, **not an executed Docker build**. We did not test pnpm 12, real dependency fetching/linking, optional dependencies, restored members, filtered installs, other operating systems, lifecycle scripts, timing or the release's security fixes. Review the selected projects and preserve a lockfile diff when adapting the recipe to your build.

Prepared with AI assistance; CyberNative AI LLC is responsible for the note. Corrections: [hello@cybernative.ai](mailto:hello@cybernative.ai). Recipe: [MIT](LICENSE).
