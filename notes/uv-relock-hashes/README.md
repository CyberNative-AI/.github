# uv 0.12.22: a new resolution can keep an old archive hash

Changing your Python requirement can force uv to resolve a project again. In our local-wheel example, uv 0.12.22 keeps the recorded hash of an unchanged dependency identity through that resolution. If the wheel's bytes have changed, installation then stops with a hash mismatch. uv 0.12.21 instead records the replacement hash during relocking and installs the replacement.

This is one change in the [0.12.22 release](https://github.com/astral-sh/uv/releases/tag/0.12.22), published on GitHub on October 2, 2026; the release-note text says October 1. The [merged fix](https://github.com/astral-sh/uv/pull/22083) describes retaining archive hashes unless the relevant dependency is selected for an unlocked upgrade. Our check below isolates a local wheel, rather than repeating that claim for every package source.

## Reproduce the difference

[Download the recipe ZIP](https://github.com/CyberNative-AI/.github/raw/refs/heads/main/notes/uv-relock-hashes/uv-relock-hashes.zip) and extract it. The ZIP contains this note, the fixture, observed results and its license.

Use a disposable directory, Python 3.12.1 or later and an official Linux x86-64 uv executable from either [0.12.21](https://github.com/astral-sh/uv/releases/tag/0.12.21) or [0.12.22](https://github.com/astral-sh/uv/releases/tag/0.12.22). Check the release's archive checksum. Keep your system installation as it is. Set `UV_RELOCK_EXE` to the absolute path of the executable you chose.

The included `make_fixture.py` creates a new directory and refuses to overwrite an existing one. Its wheel contains metadata and a text marker, with no Python code or build backend. All uv commands below are offline, disable the cache and disable Python downloads.

```sh
python3 make_fixture.py uv-relock-demo
cd uv-relock-demo
"$UV_RELOCK_EXE" --version
"$UV_RELOCK_EXE" lock --offline --no-cache --no-python-downloads --python python3
cp uv.lock before.lock
cp replacement.whl demo_pkg-1.0.0-py3-none-any.whl
python3 - <<'PY'
from pathlib import Path
p = Path('pyproject.toml')
p.write_text(p.read_text().replace('>=3.12', '>=3.12.1'))
PY
"$UV_RELOCK_EXE" lock --offline --no-cache --no-python-downloads --python python3
python3 - <<'PY'
import tomllib
from pathlib import Path
for filename in ('before.lock', 'uv.lock'):
    packages = tomllib.loads(Path(filename).read_text())['package']
    package = next(p for p in packages if p['name'] == 'demo-pkg')
    print(filename, package['wheels'][0]['hash'])
PY
"$UV_RELOCK_EXE" sync --frozen --offline --no-cache --no-python-downloads --python python3
```

On our Linux/CPython 3.12.3 run, both lock commands succeed in both versions. With 0.12.21, the second printed hash changes and frozen sync succeeds, installing the `replacement` text marker. With 0.12.22, the two printed hashes match and frozen sync exits 1 with a hash mismatch; no marker is installed. Run the other version in a new fixture directory to compare. Exact hashes, commands and outcomes are in `results.json`.

## What the controls establish

With unchanged wheel bytes and the same Python-requirement edit, both versions retain the original hash and install the original marker. In a separate fresh fixture, replacing the wheel without editing the project makes `sync --locked` refuse the hash mismatch in both versions. That control shows the older version already checks hashes when the lock remains in force; the observed difference concerns relocking.

Within the synthetic replacement fixture, `sync --upgrade-package demo-pkg` succeeds in both versions and records the replacement hash. This demonstrates the explicit upgrade boundary. It is not an instruction to silence an unexpected mismatch in a real project: first establish whether the source and replacement archive are the ones you intended to accept.

For CI that must use an existing lockfile, the [official locking and syncing guide](https://docs.astral.sh/uv/concepts/projects/sync/#automatic-lock-and-sync) distinguishes `--locked`, which checks freshness without changing the lock, from `--frozen`, which uses the existing lock without checking project freshness. Choose that behavior deliberately; neither flag makes an unreviewed archive trustworthy.

## Limits

Tested October 3, 2026 on Linux x86-64 with CPython 3.12.3 and the official uv 0.12.21/0.12.22 executables. This fixture uses one local wheel path and an unrelated Python-requirement edit. It does not test registry packages, source distributions, remote URLs, other operating systems, earlier uv versions or production CI. No speed, complete dependency-integrity or attack-prevention claim follows from it. Changing dependency identity, upgrade selection and cached execution are outside the reproduced comparison.

AI-assisted writing and fixture preparation by CyberNative AI LLC. Corrections: hello@cybernative.ai.
