# pnpm deploys: stop the second install after a frozen install

On a machine where `CI` is not set, with `autoDedupe: true`, this deploy step can install twice:

```sh
git pull
pnpm install --frozen-lockfile
pnpm run build
```

After a pull that changes a dependency, `pnpm run` starts another install before the script and runs every lifecycle script again. [pnpm/pnpm#16583](https://github.com/pnpm/pnpm/issues/16583) reports this for 12.9.0. We reran that reproduction on October 7, 2026 with four official Linux x86-64 releases.

Upgrading alone did not change the result. Two fixes worked. Each has a condition you should check first.

| | 12.9.0 | 12.9.1 | 12.10.0 | 12.10.1 |
|---|---|---|---|---|
| Default settings: postinstall runs again inside `pnpm run` | yes | yes | yes | yes |
| Fix 1, `lockfile.includeResolutionSettings: true`: postinstall runs again | cannot read the config | cannot read the config | no | no |
| Fix 2, `pnpm_config_frozen_lockfile=true` on the run step: postinstall runs again | no | no | no | no |
| Fix 2 with a stale lockfile: the script still runs | yes, exit 0 | yes, exit 0 | yes, exit 0 | yes, exit 0 |

12.10.0 and 12.10.1 print a hint that names Fix 1 when this happens.

## Fix 1: record the setting in the lockfile

12.10.0 added a setting in `pnpm-workspace.yaml`. It was merged as the fix for #16583 ([pnpm/pnpm#16591](https://github.com/pnpm/pnpm/pull/16591)):

```yaml
autoDedupe: true
lockfile:
  includeResolutionSettings: true
```

`pnpm-lock.yaml` then records `autoDedupe`. A server that runs `pnpm install --frozen-lockfile` reuses that lockfile, and `pnpm run` goes straight to the script. In our runs, 12.10.0 and 12.10.1 ran the script with no second install.

The condition: every machine that reads the repository needs pnpm 12.10.0 or later. 12.9.0 and 12.9.1 stop with `expected string scalar` while reading `pnpm-workspace.yaml`. In earlier versions, `lockfile` is only a `true`/`false` setting. [pnpm's documentation for this setting](https://pnpm.io/settings/store#lockfileincluderesolutionsettings) states the same limit.

We also pinned `"packageManager": "pnpm@12.10.1"` in `package.json`. With that pin, 12.9.0 and 12.9.1 still failed before they could switch versions. 12.10.0 switched to 12.10.1 and installed. Upgrade each deploy server and CI image before you commit the setting.

## Fix 2: mark the run step as frozen

If some machines still run 12.9.x, set the variable on the deploy machine's run step. No repository change is needed:

```sh
set -e
git pull
pnpm install --frozen-lockfile
pnpm_config_frozen_lockfile=true pnpm run build
```

The #16583 report notes that this variable, or `CI=true`, makes `pnpm run` go straight to the script. In our runs, all four versions ran the script with no second install.

The condition: the frozen install must stop the deploy when it fails. We added a dependency to `package.json` without updating the lockfile. `pnpm install --frozen-lockfile` exited 1, as it should. Then we ran `pnpm_config_frozen_lockfile=true pnpm run` anyway. The install it starts first failed, and pnpm printed a warning. Then it ran the script and exited 0, and the script could not load the new package. This warn-and-run behavior is documented in the [12.9.0 release notes](https://github.com/pnpm/pnpm/releases/tag/v12.9.0). Keep `set -e` or `&&` between the two commands so a failed frozen install stops the deploy before the build starts.

## Current status

#16583 is closed with Fix 1. A separate change for default settings, [pnpm/pnpm#16588](https://github.com/pnpm/pnpm/pull/16588), was open and unmerged when we checked on October 7. Until a release includes a change for default settings, choose one of the fixes above.

## Rerun the comparison

Download this directory. Give `check.sh` one or more pnpm executables:

```sh
bash check.sh /path/to/pnpm-12.9.0 /path/to/pnpm-12.10.1 > my-result.json
```

[`check.sh`](check.sh) builds each case in a new temporary project, with its own `HOME` and store and with `CI` unset. It installs `is-number` and `is-odd` from the npm registry, so it needs network access. It counts postinstall output lines and records exit codes. The four versions took about 20 seconds in total on our machine. [`result.json`](result.json) is our recorded output. [`binary-provenance.json`](binary-provenance.json) lists the release assets and the SHA-256 hashes we downloaded. pnpm does not publish a checksum file for these assets.

Scope: one single-package project from the issue's reproduction, Linux x86-64, the four releases above and `autoDedupe: true`. We did not test workspaces with several projects, other platforms, pnpm 11, `CI=true` or `verifyDepsBeforeRun` values other than the default. We did not measure install time. Check your own deploy script before relying on either fix.

AI-written note from CyberNative AI LLC. Questions or corrections: hello@cybernative.ai.
