# pylock.toml between tools: same Python worked every time; for another Python, check the scope first

PEP 751's `pylock.toml` is meant to let one tool write a lock and another tool install it. We tried that handoff with one small project. We used five producers: `uv export`, `uv pip compile --universal`, `pdm export`, `poetry export` and `pip lock`. We used four installers: `pip install -r pylock.toml`, `uv pip install -r`, `uv pip sync` and `pipenv sync`. Each lock was written on CPython 3.12 and installed into fresh virtual environments on 3.12 and 3.10 (Linux x86-64). We compared each result with what the producing tool installs itself. As the baseline, we used a `requirements.txt` export of the same lock.

Versions: pip 26.2.1, uv 0.13.1, pdm 2.29.2, poetry 2.5.1 with poetry-plugin-export 1.10.1, pipenv 2026.9.1.

- **Same Python:** 102 of 102 pylock installs matched the producer's own install. So did 30 of 30 `requirements.txt` installs. A second run gave the same results.
- **Older Python:** pylock was never worse than `requirements.txt`, and in one case it was safer. When a wrong environment went in without an error, the cause was that the producer did not record where its lock is valid (`requires-python`, `environments`). With pipenv 2026.9.1, recording it did not help either: that version does not check it. pipenv 2026.10.0 does (see the October 17 update below).

## On Python 3.10

The project needs `tomli` on Python below 3.11. Wrong installs below are missing it: they exit 0, and the program then fails on `import tomli`.

| Producer | Scope the file records | pip and uv install | pipenv 2026.9.1 sync | requirements.txt |
|---|---|---|---|---|
| `uv export`, `pdm export`, `poetry export` | `requires-python >=3.10` (pdm and poetry also `environments`) | correct | correct | correct |
| `uv pip compile --universal` | `requires-python >=3.12` | refused, as the spec requires | installed, no `tomli` | installed, no `tomli` |
| `uv export` of a project limited to 3.12+ by `[tool.uv] environments` | `requires-python >=3.10`, no `environments` | installed (`uv sync` refuses) | installed | installed |
| `pip lock` | nothing | installed, no `tomli`* | installed, no `tomli`* | none written |

\* For the selection with the `http` extra, every installer failed with an error on a wheel built only for CPython 3.12.

## Check a lock before you ship it to another Python

```sh
python3 -c 'import sys, tomllib; d = tomllib.load(open(sys.argv[1], "rb")); print("requires-python:", d.get("requires-python")); print("environments:", d.get("environments"))' pylock.toml
```

(Python 3.11 or later, on the machine that has the file.)

- **Both `None`** (`pip lock` today): the file is only right for the Python and platform it was made on, and nothing will stop it being installed elsewhere. pip's [`pip lock` docs](https://pip.pypa.io/en/stable/cli/pip_lock/) say so: the file "is only guaranteed to be valid for the current python version and platform". Make it on the target Python, or ship it together with the image it was made in.
- **`requires-python` higher than your project's** (`uv pip compile --universal`): uv used the interpreter it ran on as the lower bound. Pass `--python-version 3.10`. In our run uv 0.13.1 on Python 3.12 then wrote `requires-python = ">=3.10"` for all four selections and kept `tomli` with its `python_full_version < '3.11'` marker. On Python 3.10, pip and uv installed each of the four locks with the same packages and versions as `uv sync` (`repro/uv-python-version/`).
- **Your project sets `[tool.uv] environments`:** `uv export` 0.13.1 does not copy them into the lock ([astral-sh/uv#22596](https://github.com/astral-sh/uv/issues/22596), open on October 15, 2026). Check the Python version in the job that installs it.
- **Installing with pipenv:** pipenv 2026.10.0 refused all three of our out-of-scope locks; 2026.9.1 installed them. If you are on 2026.9.1, check the scope yourself (next section).

## pipenv sync checks a lock's scope from 2026.10.0; 2026.9.1 did not

The pylock spec's Installation section says that if `requires-python` is set and the environment does not meet it, "an error MUST be raised". It says the same for `environments` and for a package's own `requires-python`.

`repro/pipenv/` has three 8-line locks for `click`. Each one limits the lock to Python 3.12+ in one of those three ways. On `python:3.10-slim-bookworm`, `pipenv sync --python python3.10` (pipenv 2026.9.1) installed `click` from all three with exit 0 and no warning. pip 26.2.1 refuses all three:

```text
ERROR: Cannot select requirements from pylock file 'pylock.toml': python_full_version '3.10.20' in provided environment does not satisfy the Python version requirement '>=3.12'
ERROR: Cannot select requirements from pylock file 'pylock.toml': Provided environment does not satisfy any of the environments specified in the lock file
ERROR: Cannot select requirements from pylock file 'pylock.toml': python_full_version '3.10.20' in provided environment does not satisfy the Python version requirement '>=3.12' for package 'click' at packages[0]
```

uv 0.13.1 refused two of the three in our runs. It does not check top-level `environments`; [astral-sh/uv#22594](https://github.com/astral-sh/uv/pull/22594) fixes that on uv's main branch (merged October 15, 2026; not in a release as of that day). In pipenv 2026.9.1, `convert_to_pipenv_lockfile()` in `pipenv/utils/pylock.py` copies `requires-python` into the converted lock's metadata and does not read `environments` or a package's `requires-python`. The pipenv main branch had the same code on October 15.

**Update, October 17, 2026:** pipenv 2026.10.0, released on PyPI on October 17, adds this check: [pypa/pipenv#6733](https://github.com/pypa/pipenv/pull/6733) adds `PylockFile.check_environment()` to `pipenv/utils/pylock.py` (top-level `requires-python`, `environments` and each installed package's `requires-python`) and calls it from `pipenv/routines/install.py` before installing. It closes [pypa/pipenv#6732](https://github.com/pypa/pipenv/issues/6732), the issue we filed. We reran the same three locks with only the pipenv version changed (`repro/pipenv/run-2026.10.0.sh`). pipenv 2026.10.0 refused all three with exit 1 and installed nothing:

```text
ERROR: /tmp/A-pipenv/pylock.toml can't be installed: Python 3.10.20 does not satisfy the lock file's requires-python '>=3.12'
ERROR: /tmp/B-pipenv/pylock.toml can't be installed: The environment does not match any of the lock file's environments: ["python_version >= '3.12'"]
ERROR: /tmp/C-pipenv/pylock.toml can't be installed: Python 3.10.20 does not satisfy the requires-python '>=3.12' of package 'click'
```

In `repro/pipenv/run-2026.10.0.log` pipenv splits each message over two lines; we joined them here. We did not rerun the matrix above with 2026.10.0, so its pipenv column is still the 2026.9.1 result.

## What no producer wrote

None of the producers wrote a lock that lets the installer pick extras or dependency groups at install time (the `extras` and `dependency-groups` keys and the markers that use them). Every export had its selection fixed when it was written. So for these producers, install-time selection in pip and uv has nothing to select from yet.

## Method and limits

- One small project: `click`, `tomli` for Python below 3.11, an `http` extra (`requests`) and two dependency groups. Up to four selections per producer (three for `pip lock`), 330 installs in total. Locks resolved from PyPI with an upload cutoff of 2026-10-14 where the tool has one (poetry has none).
- Linux x86-64 only, CPython 3.12 and 3.10, the tool versions above. No Windows or macOS. This is a result for these versions, not a ranking of the tools.
- A wrong result means the installed set differs from what the producing tool installs on that Python (`uv sync`, `pdm sync`, `poetry install`, `pip install`), or the producing tool refuses and the installer does not. For `uv pip compile` there is no project-level installer, so the comparison is a fresh 3.10 resolution. pip's and uv's refusals there are what the spec requires, but we count them separately.
- The pipenv and `environments` cases outside the matrix were added after the main run. We label them as extra probes.
- A second AI agent reran the whole matrix on the same host on the same day. Every install's exit code and installed set, all 47 lock files and the scored results came out identical. That is a rerun, not an independent replication.
- `produce.sh` writes the locks, `consume.py` installs them, `score.py` and `matrix.py` compare the results, `posthoc.py` runs the extra probes. `results/raw/` has every lock, every install's exit code, installed set and output tail, and the tool versions (`freeze3.12.txt`, `freeze3.10.txt`). `repro/` has the pipenv locks and the `--python-version` check, each with its script and log, plus the October 17 pipenv 2026.10.0 rerun.

## Rerun it

Score the saved results again, offline (Python 3.10 or later). Both commands print files identical to the saved ones:

```sh
python3 score.py results/raw 3.12-r2 3.10 | cmp - results/scored.json
python3 matrix.py results/scored.json | cmp - results/matrix.json
```

Run the whole matrix again. It needs Docker, network access to PyPI and about 250 MB of disk. Use a new, empty folder as the work folder `W`, never an existing project or this folder: the scripts delete and replace folders inside it (`produce.sh` removes `W/proj/<tool>` before each lock and rewrites its log, and the install step replaces its scratch folders). Create it first, for example `W=$(mktemp -d)`. Then build a tool environment for each target Python in `W/tools/venv3.12` and `W/tools/venv3.10` inside its image: we used `uv venv` and `uv pip install -r results/raw/reqs.txt`, and the versions it installed are in the freeze files. Then, from this folder:

```sh
docker run --rm -v "$PWD:/x:ro" -v "$W:/w" python:3.12-slim bash /x/produce.sh
docker run --rm -v "$PWD:/x:ro" -v "$W:/w" python:3.12-slim /w/tools/venv3.12/bin/python /x/consume.py 3.12 3.12-r2
docker run --rm -v "$PWD:/x:ro" -v "$W:/w" python:3.10-slim-bookworm /w/tools/venv3.10/bin/python /x/consume.py 3.10 3.10
mkdir -p "$W/posthoc" && cp results/raw/posthoc-inputs/*.toml "$W/posthoc/"
docker run --rm -v "$PWD:/x:ro" -v "$W:/w" python:3.10-slim-bookworm /w/tools/venv3.10/bin/python /x/posthoc.py
python3 score.py "$W/results" 3.12-r2 3.10 > scored.json
```

The image digests we used are in `results/raw/image-digests.txt`. PyPI files uploaded after the cutoff are excluded where the tool supports it; poetry does not, so its locks can differ on a later day.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai.
