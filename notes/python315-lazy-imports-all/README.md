# Python 3.15's global lazy imports break httpx requests, the OpenAI and Anthropic clients, sympy and pandas

Python 3.15.0 (released 9 October 2026) can make every import lazy with one switch:
`python -X lazy_imports=all` or `PYTHON_LAZY_IMPORTS=all`. A module is then loaded on first use of its name instead
of at the `import` line. That is attractive for a CLI's start-up time. With the current wheels, it also makes these
ordinary calls fail on Linux, while normal mode runs every one of them:

| use | version | under `lazy_imports=all` | names kept eager that fixed it |
|---|---|---|---|
| `httpx.Client().get(...)` | httpx 0.28.1, httpcore 1.0.9 | `AttributeError: 'lazy_import' object has no attribute '__module__' …` | `httpcore` |
| `openai.OpenAI(api_key=...)` | openai 3.32.0 (httpx2/httpcore2 2.13.1) | same `__module__` error | `httpcore2,truststore` |
| `anthropic.Anthropic(api_key=...)` | anthropic 1.15.0 (httpx2/httpcore2 2.13.1) | same `__module__` error | `httpcore2,truststore` |
| `import truststore; truststore.inject_into_ssl()` | truststore 0.10.5 | `NameError: name '_api' is not defined` | `truststore` |
| `import sympy` | sympy 1.14.0 (mpmath 1.3.0) | `AttributeError: 'FPContext' object has no attribute 'zetazero'` | `mpmath,sympy` |
| `import mpmath` | mpmath 1.4.1 | same `zetazero` error | `mpmath` |
| `pd.DataFrame({"a": [1, 2]}).sum()` | pandas 3.0.6, numpy 2.5.4 | `TypeError: 'lazy_import' object is not subscriptable` | `pandas,numpy` |
| SQLAlchemy `MetaData().create_all(engine)` | SQLAlchemy 2.1.5 | `AttributeError: 'Table' object has no attribute 'dispatch'` | `sqlalchemy` |
| alembic `MigrationContext.configure(conn)` | alembic 1.20.0 | `InvalidRequestError: No such event 'connect' …` | `sqlalchemy,alembic` |
| matplotlib `ax.legend(...)` then `savefig` | matplotlib 3.11.2 | `KeyError: 'Axes:kwdoc'` | `matplotlib` |
| OpenTelemetry `MeterProvider(...)` counter | opentelemetry-sdk 1.45.1 | `ImportError: cannot import name 'AggregationTemporality' from partially initialized module …` | `opentelemetry` |
| `from google.rpc import status_pb2` | googleapis-common-protos 1.75.5, protobuf 7.36.2 | `TypeError: Couldn't build proto file into descriptor pool: Depends on file 'google/protobuf/any.proto' …` | `google` |
| `from rapidfuzz.distance import Editop` | rapidfuzz 3.14.6 | `ModuleNotFoundError: No module named 'rapidfuzz.distance._initialize_cpp_avx2'` | `rapidfuzz` |
| `from uvicorn.supervisors import ChangeReload` | uvicorn 0.54.0 | no error: picks `WatchFilesReload` though watchfiles is not installed (normal mode picks `StatReload`) | `uvicorn` |

Each row ran twice per mode with the same result; the exact lines are in [`results/round1.tsv`](results/round1.tsv)
and [`results/round2.tsv`](results/round2.tsv). The last column is the shortest list we tried that made the use behave
as in normal mode (see [the filter](#if-you-still-want-global-mode)).

This is advice for application and CLI authors who are thinking about flipping the global switch. It is not a set of
bug reports: global mode is opt-in, and SQLAlchemy's maintainers have said that running under
`PYTHON_LAZY_IMPORTS=all` "is a non-goal" ([sqlalchemy issue 13558](https://github.com/sqlalchemy/sqlalchemy/issues/13558)).

## How common is it? The top 300 PyPI projects

We installed each of the 300 most-downloaded PyPI projects (Hugo van Kemenade's
[30-day list](https://hugovk.dev/top-pypi-packages/), updated 1 October 2026; [`census/frame.txt`](census/frame.txt))
into its own environment: CPython 3.15.0 (`python:3.15.0-slim`, digest `sha256:d802f032…5313`), uv 0.13.1, binary
wheels only, index frozen at 2026-10-17 00:00 UTC. We imported each project's top-level names (up to 10, from its
wheel's RECORD), then read every attribute of every newly loaded module. Reading an attribute forces a lazy import to
load. Each project ran twice in normal mode and twice under `all`, with no network.

- 7 projects had no Python 3.15 Linux wheel at the cutoff, 2 had no importable names, and 10 did not import offline
  in normal mode. That leaves 281, of which 7 we had tried before fixing the method (calibration). **274 count.**
- **20 of the 274 raised errors under `all` that normal mode did not raise, in both repeats.** For 7 of them the
  `import` itself raised: google-cloud-aiplatform, httpcore, httpcore2, matplotlib (the `pylab` and `mpl_toolkits`
  names), mpmath, sympy, truststore. For the other 13 the error came when an attribute was first read: alembic,
  anthropic, azure-storage-blob, docker, google-cloud-bigquery, google-cloud-core, jsonschema, mcp, openai,
  opentelemetry-sdk, rapidfuzz, structlog, uvicorn. No error changed between repeats.
- Calibration: pandas, SQLAlchemy and google-cloud-storage failed; numpy, orjson, pydantic and six did not.
- Keeping each failing project's own imports eager (a filter on its own names) fixed **12 of the 20**. The other 8
  failed inside a dependency: alembic (in SQLAlchemy), azure-storage-blob (azure-core), the three google-cloud
  projects (generated protobuf modules), httpcore2 (truststore), mcp (uvicorn) and sympy (mpmath).

The 20 is a count of import-order differences, not of user harm. The attribute walk is a generic forced use: it
flagged jsonschema for optional format-checker dependencies that were simply not installed, and it missed httpx,
which only the use test above caught. The table at the top lists what we found in documented uses; we chose those
uses after seeing the census results.

## Why it breaks: five patterns

1. **Registration by import side effect never runs.** SQLAlchemy registers its event machinery, mpmath its function
   table and matplotlib its docstring fragments as modules are imported. A lazy import that nobody touches does
   not run that code. alembic then fails inside SQLAlchemy, and sympy inside mpmath. Our earlier
   [plugin registration recipe](https://github.com/CyberNative-AI/.github/tree/main/notes/python315-lazy-registration)
   shows the same pattern in a few lines of synthetic code. pandas's own open report (issue 71173) describes the
   same pattern for its initialization imports; we did not trace our pandas error to that cause.
2. **Module globals treated as values.** httpcore's `__init__.py` ends with a loop that rewrites `__module__` on
   everything it exports:

   ```python
   for __name in __all__:
       if not __name.startswith(("__", "SOCKET_OPTION")):
           setattr(__locals[__name], "__module__", "httpcore")
   ```

   Under `all`, `__locals[__name]` is the lazy placeholder, which has no `__module__` to set. httpcore2 has the same
   loop, which is how `openai.OpenAI(...)` and `anthropic.Anthropic(...)` fail. truststore does
   `from ._api import SSLContext, …` and then `del _api`; the submodule was never bound, so the `del` raises.
3. **Generated protobuf modules depend on import order** to fill the descriptor pool. All four google-cloud projects
   that failed hit this one.
4. **Optional-dependency guards stop guarding.** [PEP 810](https://peps.python.org/pep-0810/) keeps imports inside a
   `try` block eager under `all`, but not imports inside a `with` block. rapidfuzz guards its AVX2 build like this:

   ```python
   with contextlib.suppress(ImportError):
       from rapidfuzz.distance._initialize_cpp_avx2 import Editop, Editops, ...
       _imported = True
   ```

   Under `all` the import cannot fail there, `_imported` becomes `True`, the fallback never runs, and the
   `ModuleNotFoundError` arrives when you use `Editop`. A `try` one level up fails the same way: uvicorn's
   `try: from uvicorn.supervisors.watchfilesreload import WatchFilesReload` is eager, but the
   `from watchfiles import watch` inside that module is lazy, so the `except ImportError` never fires. The census
   found the `try` shape in docker (Windows named pipes), azure-core and openai/anthropic (vendored aiohttp
   transport) and structlog (greenlet), and the `with suppress` shape in jsonschema's optional format checkers.
5. **Circular imports that eager order happened to tolerate** (OpenTelemetry's metrics package).

For library authors, pattern 4 is the reusable lesson: under global mode, a `with suppress(ImportError):` around an
import does not guard it, and the `ImportError` moves to first use.

## If you still want global mode

The simplest option is the one in the repository cited below: keep only your own script's imports lazy, with a
filter that returns `importer == "__main__"`. Every library then imports its own modules eagerly, so it should avoid
the failures above, but we did not test it, and it gives up laziness inside libraries. If you want lazy imports
inside libraries too, you need a list of packages to keep eager.

[`sys.set_lazy_imports_filter`](https://peps.python.org/pep-0810/) takes a function
`(importer, name, fromlist) -> bool`; returning `False` keeps that import eager. This is the filter we tested
([`check.py`](check.py)). It keeps an import eager when the importing module or the imported module is one of the
listed names or below them, and it has to run before the imports it should affect:

```python
import sys

EAGER = ("mpmath", "sympy", "httpcore", "httpcore2", "truststore", "sqlalchemy", "alembic",
         "pandas", "numpy", "matplotlib", "opentelemetry", "google", "rapidfuzz", "uvicorn")

def _under(mod):
    return bool(mod) and any(mod == p or mod.startswith(p + ".") for p in EAGER)

def lazy_ok(importer, name, fromlist):
    return not (_under(importer) or _under(name))

sys.set_lazy_imports_filter(lazy_ok)
```

With this one list, all 14 uses in the table behaved as in normal mode, in both repeats
([`results/union.tsv`](results/union.tsv)). With only the package where the error was raised, 9 of the 14 did
([`results/round1.tsv`](results/round1.tsv)); the other 5 needed a second name
([`results/round2.tsv`](results/round2.tsv)). For example, `openai` with only `httpcore2` eager got past the
`__module__` loop and then failed on truststore's `del _api`.

A fixed list covers about half of what it has not seen. We built a list mechanically from the top-300 results
and our trial runs (the names of every failing project, including the calibration projects and polars, the top-level package of every module where an extra error appeared, and a rule
for generated `_pb2` modules; [`census/holdout/denylist.json`](census/holdout/denylist.json)) and ran the same census on the next 200
projects, ranks 301 to 500. Of 168 eligible, **15 broke under `all`**. The list fixed 8 of the 15, and 7 of the 14
it had not seen (polars had been in our trial runs). It broke nothing that `all` alone had left working. Among those
it did not fix: hypothesis, modal, opensearch-py, slack-sdk, and toolz and requests-aws4auth, which `del` a
from-imported submodule the way truststore does.

What this does not show: that a list covers your dependencies (we tested these 14 uses, not the 20 projects'
whole APIs), or that you keep much start-up gain once numpy, pandas and every `google.*` module are eager. We did not measure start-up time. Run your own test suite with `-X lazy_imports=all`
before shipping it; the uvicorn row is a reminder that a passing run can still take a different code path.

## Others who have looked

- [nazmul284/python-315-lazy-imports](https://github.com/nazmul284/python-315-lazy-imports) measured four ways to
  defer imports and swept 26 packages on 3.15.0rc2 under macOS: 4 broke (pandas, SQLAlchemy, polars, orjson). On
  3.15.0 under Linux, pandas and SQLAlchemy still fail for us; orjson passes. polars was outside our list.
  Their README also reports that a filter keeping only the script's own imports lazy
  (`lambda importer, name, fromlist: importer == "__main__"`) fixed all four and kept their CLI's start-up at 14.72 ms.
- CPython runs its own test suite in this mode in CI
  ([cpython issue 149640](https://github.com/python/cpython/issues/149640), closed 1 October 2026 "It's now tested
  in the CI").
- pandas has an open report with a reproducer,
  [pandas issue 71173](https://github.com/pandas-dev/pandas/issues/71173). In the GitHub trackers of the 20 projects that
  broke in the census, and of SQLAlchemy and google-cloud-storage, we found no report of breakage under global mode
  as of 17 October. SQLAlchemy issue 13558 is the feature request quoted above. We searched for `lazy_imports`,
  "lazy imports" and "PEP 810", and one reader read each hit by hand. We did not search the trackers of httpx,
  protobuf, polars or the projects ranked 301 to 500.

## Run it yourself

These commands download third-party wheels from PyPI and execute their code. Use a disposable isolated environment
with no credentials or private data, and run the commands from a clean directory containing only this bundle: they
mount the current directory read-only and write installed environments under `envs/`. The Docker install step has
network access; only the test runs use `--network none`. The census scripts below also install and run third-party
code; treat them the same way.

```sh
IMG=python:3.15.0-slim@sha256:d802f03223b9e00604cd54574bcac1a4638914c43683d3f0afd6ebee35f25313
docker run --rm -v "$PWD":/c:ro -v "$PWD/envs":/w/envs "$IMG" sh /c/install_envs.sh /c/cases.tsv /w/envs
for c in cases.tsv cases-round2.tsv cases-union.tsv; do
  docker run --rm --network none -v "$PWD":/c:ro -v "$PWD/envs":/w/envs:ro "$IMG" sh /c/run_cases.sh /w/envs /c/$c
done
```

[`install_envs.sh`](install_envs.sh) installs one venv per line of [`cases.tsv`](cases.tsv) (the versions we got are
in [`results/freeze/`](results/freeze/)). [`run_cases.sh`](run_cases.sh) runs [`check.py`](check.py) in normal mode,
under `all`, and under `all` with the filter, twice each, and prints one tab-separated line per run.

The census is in [`census/`](census/): the scripts as run ([`walk.py`](census/walk.py), [`run.py`](census/run.py),
[`prep.py`](census/prep.py), [`install.sh`](census/install.sh), [`analyze.py`](census/analyze.py)), three synthetic
control packages that must classify as OK, import failure and first-use failure (they did), every raw run in
[`raw-runs.tar.gz`](census/raw-runs.tar.gz), and the classifications in [`analysis.json`](census/analysis.json) and
[`analysis-armf.json`](census/analysis-armf.json). The ranks 301 to 500 run is in [`census/holdout/`](census/holdout/),
with the scripts as run for it (the same code plus the list filter). [`recount.py`](census/recount.py) recounts the classes from the raw
runs with code written separately from `analyze.py`; its output, [`recount-output.txt`](census/recount-output.txt),
matches (it lists the three controls among the breaks, which the 274 excludes), as does
[`recount-holdout-output.txt`](census/holdout/recount-holdout-output.txt) for the holdout.
[`SHA256SUMS`](SHA256SUMS) covers every file.

## Limits

Linux x86_64 only; Windows and macOS untested. One wheel resolution date. Wheel-only: projects without a 3.15 wheel
are missing, not passing. Up to 10 names per project. Two repeats per mode. A second execution of the top-300 census from a
fresh install on the same machine gave the same class for all 303 units (300 projects and 3 controls) and the same
12 of 20 filter fixes. That rerun shows the pipeline gives the same result on one machine. It is not an independent
reproduction, and nobody outside the company has rerun the census. The ranks 301 to 500 run and the use table were
each executed once (two repeats per mode) and were not part of that rerun. The uses and the filter lists were chosen after seeing the
census results. We wrote the holdout list after the top-300 results and before running ranks 301 to 500.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. We publish dated corrections when errors are
confirmed. Corrections: hello@cybernative.ai.
