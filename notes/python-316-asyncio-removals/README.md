# Python 3.16.0a1: with pytest-asyncio installed, every test errors

Python 3.16.0a1 (October 13, 2026) removes asyncio's event loop policy system and `asyncio.iscoroutinefunction()`, both deprecated since 3.14 ([What's New in 3.16, Removed › asyncio](https://docs.python.org/3.16/whatsnew/3.16.html)). The gone names are `get_event_loop_policy()`, `set_event_loop_policy()`, `AbstractEventLoopPolicy`, `DefaultEventLoopPolicy` and the two `Windows*EventLoopPolicy` classes.

If you add 3.16 to CI, the first thing you are likely to see is pytest-asyncio. With its current release (1.4.0) installed, **every test in the session errors at setup, including plain synchronous tests**:

```
ERROR test_plain.py::test_plain - AttributeError: module 'asyncio' has no attribute 'get_event_loop_policy'
```

The plugin's session-wide `event_loop_policy` fixture is autouse and calls the removed function. pytest-asyncio `main` (checked October 14) and the open PR that removes that fixture ([#1517](https://github.com/pytest-dev/pytest-asyncio/pull/1517)) still call it when they set up an event loop, so async tests keep failing on 3.16 until a release changes that.

We scanned the latest release of the 1,000 most-downloaded PyPI packages for the removed names, then ran the packages that use them on 3.16.0a1 and 3.15.0 with the same installed files.

## What breaks

Each row fails on 3.16.0a1 and works on 3.15.0. Versions are the latest on PyPI on October 14, 2026.

| Package | On 3.16.0a1 | What to do |
|---|---|---|
| pytest-asyncio 1.4.0 | Every test errors at setup, sync tests too | [`conftest.py` stopgap](#pytest-asyncio-stopgap) until a release supports 3.16 |
| backoff 2.2.1 (repository archived) | Decorating any function raises `AttributeError: module 'asyncio' has no attribute 'iscoroutinefunction'` | Move to [tenacity](https://pypi.org/project/tenacity/); [shim](#iscoroutinefunction-shim) as a stopgap |
| mock 5.2.0 | `import mock` raises `ImportError: cannot import name 'set_event_loop_policy' from 'asyncio'` | `from unittest import mock`; the standard library version has `AsyncMock` |
| cached-property 2.0.1 | Every access to a cached attribute raises `AttributeError: … 'iscoroutinefunction'` | `functools.cached_property` for sync properties; [shim](#iscoroutinefunction-shim) for async ones (fix proposed in [pydanny/cached-property#359](https://github.com/pydanny/cached-property/pull/359)) |
| nest-asyncio 1.6.0 (repository archived) | `nest_asyncio.apply()` raises `AttributeError: … 'get_event_loop_policy'` | [nest-asyncio2](https://pypi.org/project/nest-asyncio2/) 1.7.4, a maintained fork: `import nest_asyncio2; nest_asyncio2.apply()` |
| tornado 6.5.10 | `from tornado.platform.asyncio import AnyThreadEventLoopPolicy` raises `ImportError`. `IOLoop` itself works | [Give each thread its own loop](#code-that-sets-a-policy) |

These work on 3.16.0a1 in our checks: anyio, aiohttp, asgiref, freezegun, jupyter_core, posthog, pyzmq, redis.asyncio, respx, sentry-sdk and tornado's `IOLoop`. 46 of the 1,000 packages contain one of the removed names outside type stubs. Most of those uses are behind a version check, a `hasattr`, or Windows-only code.

## pytest-asyncio stopgap

Put this in your top-level `conftest.py`. It replaces the plugin's two private helpers with no-ops on 3.16 and later, and changes nothing on earlier versions. Remove it once a pytest-asyncio release supports 3.16.

```python
# Stopgap for pytest-asyncio <= 1.4.0 on Python 3.16, which removed the
# asyncio policy API. Remove once a pytest-asyncio release supports 3.16.
import sys

if sys.version_info >= (3, 16):
    import pytest_asyncio.plugin as _pa

    _pa._get_event_loop_policy = lambda: None
    _pa._set_event_loop_policy = lambda policy: None
```

With it, our sample suite (function- and module-scoped loops, async fixtures, `asyncio.timeout`, a sync test calling `asyncio.run`) passes on 3.16.0a1 with pytest-asyncio 1.4.0 and with `main` as of October 14, and still passes on 3.15.0. This only helps if you don't override the deprecated `event_loop_policy` fixture yourself. It patches private names and may stop working in a later pytest-asyncio release, which is fine for a stopgap.

If a run has no async tests, `pytest -p no:asyncio` disables the plugin instead.

## `iscoroutinefunction` shim

For a library you can't change yet, run this before importing it:

```python
import asyncio, inspect

if not hasattr(asyncio, "iscoroutinefunction"):
    asyncio.iscoroutinefunction = inspect.iscoroutinefunction
```

With it, backoff's sync and async decorators and cached-property's sync and async properties work on 3.16.0a1. It does nothing on 3.14 and 3.15, where those libraries still call the deprecated function and warn. In your own code, call `inspect.iscoroutinefunction()` directly, and mark sync wrappers of coroutine functions with `inspect.markcoroutinefunction()`.

## Code that sets a policy

The replacement for a policy is a loop factory, passed to `asyncio.run()` or `asyncio.Runner`:

```python
# before
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())

# after
asyncio.run(main(), loop_factory=asyncio.SelectorEventLoop)

# several calls on one loop
with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
    runner.run(first())
    runner.run(second())
```

For uvloop, the factory is `uvloop.new_event_loop`. For tornado's `AnyThreadEventLoopPolicy`, create the loop in the thread that needs it:

```python
def worker():
    asyncio.set_event_loop(asyncio.new_event_loop())
    IOLoop.current().run_sync(job)
```

## Find these before you install 3.16

Running your tests on 3.14 or 3.15 with deprecation warnings as errors catches most of them:

```sh
python -W error::DeprecationWarning -m pytest
```

On 3.15.0 that flags backoff, cached-property, nest-asyncio and tornado's `AnyThreadEventLoopPolicy`. **It misses the two that break whole test suites.** pytest-asyncio turns off `DeprecationWarning` around its own policy calls. mock imports `set_event_loop_policy` without calling it, and 3.15 only warns on the call. To check those, run the suite on 3.16.0a1 itself, for example `uv python install 3.16.0a1`.

## Method and limits

- Interpreters: CPython 3.16.0a1 (python.org release of October 13, 2026) and 3.15.0, both installed with `uv python install`. Linux x86-64 only. **The Windows paths, including the Windows policy classes and their replacements, are untested.**
- Scan: the latest release file of each of the top 1,000 packages by 30-day downloads ([hugovk/top-pypi-packages](https://github.com/hugovk/top-pypi-packages), list of October 1, 2026), searched for the removed names in `.py` and `.pyx` files. A match is a reference, not a break; the table lists only runtime failures.
- Runs: packages installed from wheels only; each check runs in a fresh process with the same installed files on both interpreters. Packages that could not install from wheels on 3.16 (uvloop, scikit-learn, twisted, fastapi and others in `results/install-316.txt`) were not run.
- This is an alpha. Python 3.16.0 final is planned for October 5, 2027 ([PEP 826](https://peps.python.org/pep-0826/)), and the packages above may release fixes before then.
- `scripts/` holds the scan and check scripts; `results/` holds their output.
