# uv 0.12.22: check the lockfile before trusting member defaults

A frozen workspace sync can select a different dependency group from an ordinary sync. uv 0.12.22 fixes that for revision-5 and later lockfiles; upgrading the executable while keeping an older lockfile can preserve the old selection.

This matters if CI runs `uv sync --package your-member --frozen` from a workspace root with different default groups. Compare the planned packages before assuming the member's development tools will be installed.

The [0.12.22 release](https://github.com/astral-sh/uv/releases/tag/0.12.22) lists the fix and new lockfile metadata. GitHub records publication on October 2, 2026; its release notes say October 1. [The upstream explanation](https://github.com/astral-sh/uv/pull/22015) identifies the root-versus-member mismatch and the revision-5 boundary.

## What we checked

On Linux x86_64 with CPython 3.12.3, we created a synthetic workspace: the root defaults to `dev`, the selected member defaults to `docs`, and each group contains a distinct empty marker wheel. Both groups exist on the member. The wheels contain metadata only; they are not real development tools.

- **0.12.21, generated revision-3 lock:** ordinary member sync selects `docs-marker`; frozen member sync selects `dev-marker`.
- **0.12.22, generated revision-5 lock:** ordinary and frozen member sync both select `docs-marker`.
- **0.12.22, unchanged revision-3 lock from 0.12.21:** frozen member sync still selects `dev-marker`.

These are observed package selections, not a speed benchmark. We also ran actual frozen installs with each executable and checked the installed marker metadata: `dev-marker` for 0.12.21 and `docs-marker` for 0.12.22 with its fresh lock.

## Rerun the small example

Obtain the official Linux executables from the [0.12.21 release](https://github.com/astral-sh/uv/releases/tag/0.12.21) and [0.12.22 release](https://github.com/astral-sh/uv/releases/tag/0.12.22). Verify their published archive checksums. Do not replace your system installation for this exercise. Set `DEMO_UV_OLD` and `DEMO_UV_NEW` to the two extracted executables, and run from this directory with Python 3.12 or later:

```sh
python3 make_fixture.py old-example
python3 make_fixture.py new-example

(cd old-example && "$DEMO_UV_OLD" lock --offline --python python3)
(cd old-example && "$DEMO_UV_OLD" sync --package release-member --offline --dry-run --python python3)
(cd old-example && "$DEMO_UV_OLD" sync --package release-member --frozen --offline --dry-run --python python3)

(cd new-example && "$DEMO_UV_NEW" lock --offline --python python3)
(cd new-example && "$DEMO_UV_NEW" sync --package release-member --frozen --offline --dry-run --python python3)

# Read the old lock with the new executable; do not regenerate it here.
(cd old-example && "$DEMO_UV_NEW" sync --package release-member --frozen --offline --dry-run --python python3)
```

Read the `revision =` line in each `uv.lock` and the marker named in each plan. Expected order: `docs-marker`, `dev-marker`, `docs-marker`, `dev-marker`. The setup refuses an existing example directory. Locking writes only inside these examples; sync uses `--dry-run`. The fixture disables package indexes and uses its local wheels. Run this in disposable examples, not inside a production project.

## Make the intended group explicit

In this example, the following selects `docs-marker` with both versions while keeping normal project-dependency selection:

```sh
uv sync --package release-member --frozen --no-default-groups --group docs --offline --dry-run --python python3
```

For a real project, choose the group your job actually needs and inspect the dry run. An alternative is to regenerate and review the lock with the new version in your normal change process. Check the resulting lock revision; upgrading the executable alone did not change our older-lock result.

`--frozen` also skips the freshness check. After changing the member's default to `dev`, our revision-5 frozen sync still selected the recorded `docs` group. `--locked` refused the stale lock with exit 1. Choose `--locked` when stale project metadata must fail rather than be ignored. See [locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/) and [default groups](https://docs.astral.sh/uv/concepts/projects/dependencies/#default-groups).

Limits: one synthetic workspace, two Linux executables and one Python version. We did not test revision 4 locally, missing member manifests, group-specific Python requirements, other operating systems, real package imports or a deployed CI job. The upstream fix describes a broader boundary than this local check.

CyberNative AI LLC · AI-assisted preparation · Corrections: hello@cybernative.ai
