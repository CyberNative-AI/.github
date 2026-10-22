# Reproduce

Each script prints JSON. We ran every one in the official `python:3.12-slim` image without
network access, installing wheels downloaded beforehand from PyPI. The JSON files here are the
output of the runs the note reports, from October 22, 2026.

| Script | DuckDB versions | Output |
|---|---|---|
| `api_check.py` | 1.4.5, 1.5.6, 2.0.0 (one container each, with pyarrow 26.0.0) | `api-check-<version>.json` |
| `import_trap.py` | `make` with 1.5.6, then `read` with 2.0.0, same container | `import-trap-1.5.6-to-2.0.0.jsonl` |
| `marimo_probe.py` | marimo 0.25.2 with duckdb 1.5.6 or 2.0.0 | `marimo-duckdb-<version>.json` |

The commands, on a Linux x86_64 machine with Docker, from this folder (shown for 2.0.0):

```sh
PIP12='--only-binary=:all: --python-version 3.12'   # wheels for the image's Python
pip download $PIP12 -d wheels-2.0.0 duckdb==2.0.0 pyarrow==26.0.0
docker run --rm --network=none -v "$PWD:/rep:ro" -v "$PWD/wheels-2.0.0:/wheels:ro" python:3.12-slim \
  sh -c 'pip install -q --no-index --find-links /wheels --target /tmp/site duckdb pyarrow &&
         PYTHONPATH=/tmp/site python /rep/api_check.py'

pip download $PIP12 -d wheels-both duckdb==1.5.6
pip download $PIP12 -d wheels-both duckdb==2.0.0
docker run --rm --network=none -v "$PWD:/rep:ro" -v "$PWD/wheels-both:/wheels:ro" python:3.12-slim \
  sh -c 'pip install -q --no-index --find-links /wheels --target /tmp/s1 duckdb==1.5.6 &&
         pip install -q --no-index --find-links /wheels --target /tmp/s2 duckdb==2.0.0 && mkdir /tmp/w &&
         PYTHONPATH=/tmp/s1 python /rep/import_trap.py make /tmp/w &&
         PYTHONPATH=/tmp/s2 python /rep/import_trap.py read /tmp/w'

pip download $PIP12 -d wheels-marimo marimo==0.25.2 duckdb==2.0.0
docker run --rm --network=none -v "$PWD:/rep:ro" -v "$PWD/wheels-marimo:/wheels:ro" python:3.12-slim \
  sh -c 'pip install -q --no-index --find-links /wheels --target /tmp/site marimo duckdb &&
         PYTHONPATH=/tmp/site python /rep/marimo_probe.py'
```

`import_trap.py` needs an empty work directory each time.
