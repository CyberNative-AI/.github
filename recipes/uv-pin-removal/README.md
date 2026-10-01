# uv python pin --rm: check the file it removes

CyberNative AI LLC · Checked October 1, 2026 · Linux x86_64

With uv 0.10.7, removing a pin from a project with no local pin also removed
our synthetic **global `.python-versions` file**. The command returned success.
The same check with a global `.python-version` file returned an error and
preserved its bytes. One extra `s` changed the deletion scope.

[uv 0.12.21, released September 29](https://github.com/astral-sh/uv/releases/tag/0.12.21),
lists a fix for this behavior. The [upstream change and regression test](https://github.com/astral-sh/uv/pull/21992/files)
recognize both filenames as global. We reproduced the older behavior on
0.10.7; **we did not execute 0.12.20 or 0.12.21**. This is a legacy observation
and a way to check your chosen executable, not our verification of the fix.

## What the local check showed

The [recorded result](legacy-result.json) contains five synthetic cases:

- Only global `.python-versions`: exit 0; the global file disappeared.
- Only global `.python-version`: exit 2; the global file stayed byte-identical.
- Local `.python-versions` plus global `.python-versions`: exit 0; only the local file disappeared.
- Local `.python-version` plus global `.python-versions`: exit 0; only the local file disappeared.
- Explicit `--global` with global `.python-versions`: exit 0; the global file disappeared.

An exit code alone cannot tell you whether cleanup stayed local. Check the
file location and the executable version before adapting pin cleanup to a
workflow. Removing a pin file is not uninstalling a Python interpreter.

## Check a chosen uv executable

Use Python 3 and an already-installed, supported uv executable that you trust
on Linux. Save these files together, then run:

```sh
python3 check_pin_scope.py "$(command -v uv)"
```

To compare another already-available uv executable that you trust, pass its
full path. The [script](check_pin_scope.py) first runs `uv --version` with your
current environment and working directory, without a timeout. It then creates
a temporary project and synthetic XDG configuration, cache, data and state
locations. The five removal commands use offline mode, disable Python downloads,
select an empty configuration file and have a ten-second timeout. Their
environment contains only PATH and the four synthetic XDG locations.

The recipe runs the executable with your user permissions; use only a trusted
uv executable. Temporary test files are cleaned up when the removal check exits.
Read the script before running it; do not run its removal commands by hand
against your real global configuration.

uv documents its [configuration locations](https://docs.astral.sh/uv/reference/storage/#configuration-directories)
and the distinction between [pin files and installing Python](https://docs.astral.sh/uv/concepts/python-versions/).
Our observations cover synthetic pin-file deletion on one Linux executable.
They do not establish behavior on other versions or platforms, interpreter
selection, package resolution, installation, or customer workflows.

This is original AI-assisted work checked within CyberNative AI LLC; no
outside reproduction is claimed. If you report a different result, include
only your uv version, platform and case name with file-presence results.
Do not include configuration contents, source files or customer data.
Corrections: hello@cybernative.ai.

The recipe's original files are covered by the [MIT license](LICENSE).
uv and the linked upstream material retain their own licenses; no uv binary
is included.
