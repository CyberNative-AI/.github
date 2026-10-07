# Python JSON guards: `value > limit` admits NaN

If your guard script reads a number from JSON and refuses only when `value > limit`, a `NaN` in the file passes it. So does `-Infinity`. A parse-time fix that rejects the `NaN` literal still misses a value like `-1e999`. Adding `math.isfinite()` without type handling can admit `true`, and it can crash on a very large integer before your cleanup runs.

None of this is new. These are documented Python and `json` behaviors. This note gives a small runnable regression file that checks all of these cases against one guard.

## Why the guard admits NaN

Python's [comparison rules](https://docs.python.org/3/reference/expressions.html#value-comparisons) say that "any ordered comparison of a number to a not-a-number value is false". `nan > 3600` is false, so a guard that only refuses on `>` admits the value.

Infinity is different. `inf > 3600` is true, so the same guard refuses `+Infinity`. `-inf > 3600` is false, so it admits `-Infinity`. An upper bound alone does not define a valid range, and it does not reject non-finite values.

The values come from ordinary JSON input. Python's `json` module [accepts and writes `NaN`, `Infinity` and `-Infinity` by default](https://docs.python.org/3/library/json.html#infinite-and-nan-number-values), even though the JSON RFC does not allow them. `json.dumps(float("nan"))` returns `NaN` unless you pass `allow_nan=False`. A state file written by another Python process can contain it.

## Why the obvious fixes fall short

**Reject the literals while parsing.** [`parse_constant`](https://docs.python.org/3/library/json.html#json.load) is called only for the strings `NaN`, `Infinity` and `-Infinity`. A number like `1e999` is parsed as a float and becomes infinity without that callback. With an upper bound only, `-1e999` is still admitted. Raising an exception from the callback also stops the script instead of producing a refusal.

**Add `math.isfinite()`.** [`math.isfinite`](https://docs.python.org/3/library/math.html#math.isfinite) works on floats. In the run below, a 401-digit JSON integer, which is a valid Python `int`, makes it raise `OverflowError` because the value is too large for a float. `math.isfinite(True)` returns `True`, and `True` compares as `1`, so a JSON `true` is admitted as one second. A string such as `"600"` raises `TypeError`.

**An exception is not a refusal.** If the guard raises, any code after it is skipped, including a step that releases a lock or restores a safe default. That step runs only if the guard returns a refusal, or if the step is in a `finally` block.

## A guard for one stated schema

The example schema has one required field. `timeout_seconds` must be a JSON number (an `int` or `float`, not a boolean or a string) with a finite value from 1 to 3600 inclusive. Any other input is refused.

```python
def safe(text):
    """Admit only a finite int/float in range; every other input is refused."""
    try:
        state = json.loads(text)
    except (ValueError, RecursionError):  # malformed, too many digits, too deep
        return "refuse: unparseable"
    if not isinstance(state, dict) or "timeout_seconds" not in state:
        return "refuse: missing field"
    value = state["timeout_seconds"]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "refuse: wrong type"
    if isinstance(value, float) and not math.isfinite(value):
        return "refuse: non-finite"
    # int/float comparison is exact in Python, so a huge int cannot overflow here.
    if not MIN_SECONDS <= value <= MAX_SECONDS:
        return "refuse: out of range"
    return "admit"
```

The order is important. The type is checked before the comparison, so a string cannot raise `TypeError` and a boolean cannot become `1`. Finiteness is checked only on floats, so a huge integer never goes through float conversion. Python [compares `int` and `float` values without loss of precision](https://docs.python.org/3/reference/expressions.html#value-comparisons), so the range check refuses that integer without error. Since Python 3.11, `json` [limits the length of integer strings](https://docs.python.org/3/library/json.html#json.load). A 5000-digit integer raises `ValueError` while parsing, and the guard turns that into a refusal. Very deep nesting raises `RecursionError`, which is not a `ValueError`, so the guard catches it as well.

## Run the regressions

[`numeric_guard_regressions.py`](numeric_guard_regressions.py) contains the original guard, the two partial fixes and the guard above. It runs each one on 17 fabricated inputs and asserts the expected results. It uses only the standard library, reads no files and makes no network connections. Do not run it with `-O`, because `-O` removes `assert` statements.

```sh
python3 numeric_guard_regressions.py
```

Observed on October 7, 2026, with CPython 3.12.3 on Linux (exit status 0):

```text
Python 3.12.3 CPython
nan > 3600, nan < 3600, nan >= 3600, nan <= 3600: False False False False
inf > 3600, -inf > 3600: True False
json.dumps(nan): NaN

case                  before                parse_only            isfinite_only         safe                 
in range int 600      admit                 admit                 admit                 admit                
in range float 1.5    admit                 admit                 admit                 admit                
upper bound 3600      admit                 admit                 admit                 admit                
finite too large 7200 refuse: too large     refuse: too large     refuse: bad value     refuse: out of range 
finite too small 0    admit                 admit                 admit                 refuse: out of range 
NaN                   admit                 CRASH ValueError      refuse: bad value     refuse: non-finite   
Infinity              refuse: too large     CRASH ValueError      refuse: bad value     refuse: non-finite   
-Infinity             admit                 CRASH ValueError      refuse: bad value     refuse: non-finite   
1e999                 refuse: too large     refuse: too large     refuse: bad value     refuse: non-finite   
-1e999                admit                 admit                 refuse: bad value     refuse: non-finite   
401-digit int         refuse: too large     refuse: too large     CRASH OverflowError   refuse: out of range 
5000-digit int        CRASH ValueError      CRASH ValueError      CRASH ValueError      refuse: unparseable  
100000-deep list      CRASH RecursionError  CRASH RecursionError  CRASH RecursionError  refuse: unparseable  
string "600"          CRASH TypeError       CRASH TypeError       CRASH TypeError       refuse: wrong type   
boolean true          admit                 admit                 admit                 refuse: wrong type   
null                  CRASH TypeError       CRASH TypeError       CRASH TypeError       refuse: wrong type   
missing field         CRASH KeyError        CRASH KeyError        CRASH KeyError        refuse: missing field

all assertions passed
```

`CRASH` means the guard raised, so a caller's recovery step after it would not run.

## Adapting it

Copy the `CASES` list for your own field and add a row for each type and boundary your schema allows. Keep the non-finite, overflow, nesting, boolean and missing-field rows. Then add your own guard function to `GUARDS`. If your guard reads several numeric fields, each one needs its own type, finiteness and range checks.

Scope: this is one guard for one fabricated single-field schema, tested on CPython 3.12.3. It is not a general secure JSON parser, a static analysis rule or a statement about any other product. Passing these rows does not prove that a different guard is correct. Other runtimes, `Decimal` or NumPy values, and schemas with several or nested fields are not tested.

AI-written note from CyberNative AI LLC. Questions or corrections: hello@cybernative.ai.
