# Python 3.15 lazy imports: check plugin registration first

A lazy import can leave your plugin registry empty until you use the imported name. Check registration before measuring startup.

This small recipe reproduces that behavior on **CPython 3.15.0rc2**, using the [October 1, 2026 standalone build](https://github.com/astral-sh/python-build-standalone/releases/tag/20261001). It is a prerelease demonstration, not a production-upgrade recommendation or a claim that Python 3.15 final has shipped.

## Run the example

Download [the recipe ZIP](./recipe.zip), extract it, and open the extracted directory with CPython 3.15.0rc2 available as `python3.15`. The example uses only the standard library.

```sh
python3.15 --version
python3.15 -B run_checks.py
```

The runner starts a fresh process for each example, clears `PYTHON_LAZY_IMPORTS` in those child processes, and selects `-X lazy_imports=normal`. It refuses another interpreter version so the recorded result has a precise target. It does not change your interpreter or install packages.

## What the test shows

`plugin.py` registers an `echo` handler at module scope. The eager control sees it immediately. In `lazy.py`, reading the registry alone does not use the imported `plugin` name:

```python
import registry
lazy import plugin

assert registry.HANDLERS == {}
assert plugin.READY is True
assert sorted(registry.HANDLERS) == ["echo"]
```

The first access to `plugin.READY` runs the module and populates the registry. The recorded output is:

```text
eager: registered before use
lazy: registry empty before first use
lazy: registered after first use
explicit: registered at initialization
filter: plugin stays eager
PASS: eager control, deferred registration, explicit initialization, eager filter
```

The two alternatives preserve registration deliberately:

- `explicit.py` calls `explicit_plugin.register(registry.HANDLERS)` before dispatch. Registration is an initialization step you can test.
- `filter.py` uses `sys.set_lazy_imports_filter` to keep this side-effect-dependent plugin eager even though its import is marked lazy. The filter is process-wide; it belongs in application initialization, not an unrelated library's import path.

For your own CLI, assert that each required command is registered before dispatch, then run an actual command. A passing `--help` path alone does not exercise a plugin that it never loads.

## Scope and sources

The [Python 3.15 documentation](https://docs.python.org/3.15/whatsnew/3.15.html#pep-810-explicit-lazy-imports) describes loading at first use. [PEP 810](https://peps.python.org/pep-0810/#how-do-lazy-imports-affect-modules-with-import-time-side-effects) covers registration side effects and explicit initialization.

These are synthetic modules, not a reproduced defect in a third-party CLI. We did not measure startup speed, check final-release behavior, test global `lazy_imports=all`, or validate a production migration. The eager control, deferred-registration example and both initialization alternatives pass on the named Linux x86-64 build.

CyberNative AI LLC · Corrections: hello@cybernative.ai
