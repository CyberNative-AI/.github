"""Before/after regressions for a JSON-backed numeric guard.

Fabricated schema for this example only: a JSON object with one required
field, "timeout_seconds", which must be a JSON number (int or float, not a
boolean or string) with a finite value from 1 to 3600 inclusive.

Each guard returns "admit" or a refusal. The caller proceeds on "admit" and
runs its recovery step (for example, releasing a lock) on any refusal. A guard
that raises skips that recovery step; this script reports it as CRASH.

Standard library only. Reads no files and opens no network connections.
Run: python3 numeric_guard_regressions.py   (not with -O, which strips assert)
"""

import json
import math
import platform

MIN_SECONDS = 1
MAX_SECONDS = 3600


def before(text):
    """Original guard: reject only if the value exceeds the limit."""
    value = json.loads(text)["timeout_seconds"]
    if value > MAX_SECONDS:
        return "refuse: too large"
    return "admit"


def _reject_constant(name):
    raise ValueError(f"non-finite literal {name}")


def parse_only(text):
    """Partial fix: reject the NaN/Infinity literals while parsing."""
    value = json.loads(text, parse_constant=_reject_constant)["timeout_seconds"]
    if value > MAX_SECONDS:
        return "refuse: too large"
    return "admit"


def isfinite_only(text):
    """Partial fix: add a finiteness check, without type or overflow handling."""
    value = json.loads(text)["timeout_seconds"]
    if not math.isfinite(value) or value > MAX_SECONDS:
        return "refuse: bad value"
    return "admit"


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


def outcome(guard, text):
    """Run the guard the way a caller would and record which path was reached."""
    try:
        verdict = guard(text)
    except Exception as error:  # the caller's recovery step is never reached
        return f"CRASH {type(error).__name__}"
    return verdict


HUGE_INT = "1" + "0" * 400        # 401 digits: parses, too large for a float
OVER_DIGIT_LIMIT = "1" * 5000     # over CPython's default 4300-digit limit
DEEP_NESTING = "[" * 100000 + "]" * 100000  # valid JSON, too deep to parse

CASES = [
    # (label, JSON document, should the safe guard admit it?)
    ("in range int 600", '{"timeout_seconds": 600}', True),
    ("in range float 1.5", '{"timeout_seconds": 1.5}', True),
    ("upper bound 3600", '{"timeout_seconds": 3600}', True),
    ("finite too large 7200", '{"timeout_seconds": 7200}', False),
    ("finite too small 0", '{"timeout_seconds": 0}', False),
    ("NaN", '{"timeout_seconds": NaN}', False),
    ("Infinity", '{"timeout_seconds": Infinity}', False),
    ("-Infinity", '{"timeout_seconds": -Infinity}', False),
    ("1e999", '{"timeout_seconds": 1e999}', False),
    ("-1e999", '{"timeout_seconds": -1e999}', False),
    ("401-digit int", '{"timeout_seconds": %s}' % HUGE_INT, False),
    ("5000-digit int", '{"timeout_seconds": %s}' % OVER_DIGIT_LIMIT, False),
    ("100000-deep list", '{"timeout_seconds": %s}' % DEEP_NESTING, False),
    ('string "600"', '{"timeout_seconds": "600"}', False),
    ("boolean true", '{"timeout_seconds": true}', False),
    ("null", '{"timeout_seconds": null}', False),
    ("missing field", "{}", False),
]

GUARDS = [before, parse_only, isfinite_only, safe]


def main():
    print("Python", platform.python_version(), platform.python_implementation())

    nan = float("nan")
    print("nan > 3600, nan < 3600, nan >= 3600, nan <= 3600:",
          nan > 3600, nan < 3600, nan >= 3600, nan <= 3600)
    print("inf > 3600, -inf > 3600:", math.inf > 3600, -math.inf > 3600)
    print("json.dumps(nan):", json.dumps(nan))
    print()

    width = max(len(label) for label, _, _ in CASES)
    print("case".ljust(width), *(g.__name__.ljust(21) for g in GUARDS))
    results = {}
    for label, text, _ in CASES:
        row = {g.__name__: outcome(g, text) for g in GUARDS}
        results[label] = row
        print(label.ljust(width), *(row[g.__name__].ljust(21) for g in GUARDS))

    # The original bypass and the two partial fixes, as regressions.
    assert results["NaN"]["before"] == "admit"
    assert results["-Infinity"]["before"] == "admit"
    assert results["Infinity"]["before"] == "refuse: too large"
    assert results["1e999"]["parse_only"] == "refuse: too large"
    assert results["-1e999"]["parse_only"] == "admit"
    assert results["401-digit int"]["isfinite_only"] == "CRASH OverflowError"
    assert results["boolean true"]["isfinite_only"] == "admit"

    # The safe guard admits exactly the in-range controls and never raises.
    for label, _, should_admit in CASES:
        verdict = results[label]["safe"]
        assert not verdict.startswith("CRASH"), (label, verdict)
        assert (verdict == "admit") == should_admit, (label, verdict)
    print()
    print("all assertions passed")


if __name__ == "__main__":
    main()
