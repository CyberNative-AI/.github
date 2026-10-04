# uv 0.12.23: read the dependency tree without the manifest

A `uv.lock` copied out of a Python project can now tell you its recorded dependency tree, even when `pyproject.toml` is missing. In our offline example, uv 0.12.23 prints the same tree from a directory containing only the lockfile that uv 0.12.22 prints from the complete project. The older version rejects the lockfile-only directory.

This is a preview change in the [October 3, 2026 release](https://github.com/astral-sh/uv/releases/tag/0.12.23). The [merged tree change](https://github.com/astral-sh/uv/pull/22016) adds manifest-free discovery for `uv tree --frozen`. That is useful when a reviewer receives a lockfile as a build artifact: start with the recorded graph before trying to reconstruct the project.

## Try the recorded graph

[Download the recipe ZIP](https://github.com/CyberNative-AI/.github/raw/refs/heads/main/notes/uv-lock-without-manifest/uv-lock-without-manifest.zip) and extract it. It contains this note, the example lockfile, fixture scripts, observed results and license. uv executables are not bundled.

Use an official Linux x86-64 uv 0.12.23 executable from the release and verify its archive checksum. Keep your system installation as it is. Set `UV_TREE_EXE` to the absolute path of that executable and `UV_TREE_PYTHON` to the absolute path of an existing Python 3.12 or later interpreter. Our check used CPython 3.12.3. Use the interpreter path explicitly: uv's interpreter discovery can select a different version from a bare `python3` request.

Copy the included `standalone.lock` into a **new disposable directory** as `uv.lock`. With that directory as your current directory, run:

```sh
"$UV_TREE_EXE" tree --frozen --offline --no-cache --no-python-downloads --python "$UV_TREE_PYTHON"
```

The observed tree is:

```text
lock-inspection-demo v0.1.0
└── demo-parent v1.0.0
    └── demo-leaf v1.0.0
```

The command also warns that using the lockfile without the manifest is experimental. Add `--preview-features frozen-lockfile` to suppress that warning. In this check the flag did **not** unlock a command that otherwise failed: both forms exited 0 and printed the same tree. The [preview guide at the release pin](https://github.com/astral-sh/uv/blob/46b84fd0bfec23b72f29e8e2185ba68a65052f48/docs/concepts/preview.md#using-preview-features) explains this warning behavior.

With uv 0.12.22, the first command exits 2 because it cannot find `pyproject.toml`. On 0.12.23, removing `--frozen` also fails in this directory. An empty directory fails with or without the manifest-free feature: it cannot supply the missing lockfile.

## Recreate the comparison

The included `make_fixture.py` creates two metadata-only wheels and a project manifest. The parent declares a dependency on the leaf. Neither wheel contains Python code or a build backend. `verify.py` creates a fresh fixture, generates a real lockfile from those local wheels, and compares the two executables. It refuses to overwrite its output directory.

From this note's directory, set `UV_TREE_OLD` and `UV_TREE_NEW` to the absolute executable paths for 0.12.22 and 0.12.23, then run:

```sh
"$UV_TREE_PYTHON" verify.py --old "$UV_TREE_OLD" --new "$UV_TREE_NEW" --output tree-comparison
```

The lock generation uses `--no-index --find-links .`; every uv command is offline, disables the cache and disables Python downloads. The comparison directory holding only `uv.lock` contains no wheels or manifest. Its lockfile stays byte-for-byte unchanged, and no installed environment is created. The retained commands, exit codes and output are in `results.json`.

## The boundary: description is not installation

We also ran `uv export --frozen --preview-features frozen-lockfile --no-hashes` in that lockfile-only directory, with the same offline controls. It printed `demo-leaf==1.0.0` and `demo-parent==1.0.0` even though the wheel files were absent. That output describes dependencies; it does not establish that the files needed to install them are available. We did not run sync or install the exported requirements.

This synthetic Linux example tests one dependency edge with uv 0.12.22/0.12.23 and CPython 3.12.3. It does not test registry downloads, dependency groups, workspace members, platform markers, other operating systems or production CI. It measures neither speed nor package integrity. Reading the locked graph does not verify that it is current or that an installed environment matches it.

AI-assisted writing and fixture preparation by CyberNative AI LLC. Corrections: hello@cybernative.ai.
