# pwasm fuel counts calls and loops, not instructions

Before you use pwasm's fuel counter to budget a workload, check what one unit means. Two tiny WebAssembly modules in this recipe each consume **12 fuel units**, although one contains **1 accumulator addition per loop body** and the other contains **65**. Their results are **10** and **650**. Fuel is a repeatable work counter; converting it to an instruction count or a duration would misread this result.

[pwasm 0.2a0 was uploaded on October 1, 2026](https://pypi.org/project/pwasm/0.2a0/). It is an alpha WebAssembly runtime written in Python. This check uses that exact distribution, rather than a moving branch.

## Run the check

Download `check_fuel.py` and `requirements.txt` from this directory. In a new directory on Linux with Python 3.10 or later:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --only-binary=:all: --no-deps --require-hashes -r requirements.txt
PWASM_CACHE_DIR='' .venv/bin/python check_fuel.py > result.json
```

Package installation requires access to PyPI. The check itself creates its own small modules and uses no guest interpreters, imported host functions, files from a user or network requests. The empty `PWASM_CACHE_DIR` setting disables pwasm's compiled-code disk cache for this run. [Upstream documents that setting](https://github.com/simonw/pwasm/tree/3398e812b0fffe4db8dbf1eb2df2d7b60ec7dad7#compiling-to-python).

## What we observed

On Linux with CPython 3.12.3, `proof.stdout.json` records both modules in `interpret`, `compile` and `auto` modes, with three calls per instance. All **18 calls** returned the expected accumulator total and consumed **12 fuel units per call**. Each module runs its nonzero loop body ten times, then enters the loop once more to test zero and exit. That is eleven loop entries plus one function call.

The script also checks **six exhaustion controls**: with a budget of five units, both modules raise `OutOfFuel` in each mode with five units consumed. **Three expired-deadline controls** raise `Timeout`, one per mode. These controls check exhaustion and an already-expired deadline; they do not measure how promptly a deadline interrupts real work.

This agrees with the pinned [`Limits` implementation](https://github.com/simonw/pwasm/blob/3398e812b0fffe4db8dbf1eb2df2d7b60ec7dad7/src/pwasm/runtime.py#L162-L242). Fuel charges are present in both the [interpreter](https://github.com/simonw/pwasm/blob/3398e812b0fffe4db8dbf1eb2df2d7b60ec7dad7/src/pwasm/executor.py#L385-L389) and [generated Python](https://github.com/simonw/pwasm/blob/3398e812b0fffe4db8dbf1eb2df2d7b60ec7dad7/src/pwasm/codegen.py#L1390-L1394).

## Use the result

Keep fuel and elapsed-time limits separate. If your workload needs both, pass `Limits(fuel=..., check_interval=...)` and set a deadline with `limits.set_deadline(time.monotonic() + seconds)`. Choose the budgets for your actual code. This recipe sets `check_interval=1` to make its controls easy to inspect; it does not establish a suitable interval for another application.

**Limit:** these are authored arithmetic modules with no memory or host imports. We did not test MicroPython, QuickJS, WASI, host callbacks, malformed inputs, memory limits, deadline latency or another Python/platform combination. This is neither a speed comparison nor a security assessment. A passing result does not certify arbitrary code as safe to run.

If you get a different result, retain the distribution version, Python version, mode and failing assertion. Keep private inputs out of a public report.

This recipe and its recorded result are [MIT licensed](LICENSE). It imports pwasm; no pwasm distribution or guest interpreter is included here.
