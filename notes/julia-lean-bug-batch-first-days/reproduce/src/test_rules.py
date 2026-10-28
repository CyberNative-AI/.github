"""Fixture controls for the frozen outcome rules (run: python3 -I src/test_rules.py)."""
import datetime as dt
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import compute as c  # noqa: E402

RT = dt.datetime(2026, 10, 28, 12, tzinfo=dt.timezone.utc)
base = {"number": 1, "created_at": "2026-10-27T03:00:00Z", "closed_at": None, "merged_at": None, "is_pr": True}
cases = [
    ({}, 24, "OPEN"),
    ({"merged_at": "2026-10-27T20:00:00Z", "closed_at": "2026-10-27T20:00:00Z"}, 24, "ACCEPTED"),
    ({"merged_at": "2026-10-28T04:00:00Z", "closed_at": "2026-10-28T04:00:00Z"}, 24, "OPEN"),
    ({"closed_at": "2026-10-27T05:00:00Z"}, 24, "CLOSED_UNACCEPTED"),
    ({"closed_at": "2026-10-27T05:00:00Z", "xref_prs": [{"number": 9, "merged_at": "2026-10-27T10:00:00Z"}]}, 24, "ACCEPTED"),
    ({"closed_at": "2026-10-27T05:00:00Z", "closed_commit_ids": ["abc"]}, 24, "ACCEPTED"),
    ({}, 72, None),
    ({"is_pr": False, "closed_at": "2026-10-27T05:00:00Z", "state_reason": "completed"}, 24, "COMPLETED_NOFIX"),
    ({"is_pr": False, "closed_at": "2026-10-27T05:00:00Z", "state_reason": "completed",
      "xref_prs": [{"number": 9, "merged_at": "2026-10-27T05:00:00Z"}]}, 24, "ACCEPTED"),
    ({"is_pr": False, "closed_at": "2026-10-27T05:00:00Z", "state_reason": "completed",
      "xref_prs": [{"number": 9, "merged_at": "2026-10-27T09:00:00Z"}]}, 24, "COMPLETED_NOFIX"),
    ({"is_pr": False, "closed_at": "2026-10-27T05:00:00Z", "state_reason": "not_planned"}, 24, "NOT_PLANNED"),
]
bad = 0
for over, h, want in cases:
    r = dict(base, **over)
    got = c.outcome(r, h, RT)
    if got != want:
        bad += 1
        print("FAIL", over, h, got, want)
assert abs(c.fisher(3, 10, 3, 10) - 1.0) < 1e-9
assert abs(c.fisher(10, 10, 0, 10) - 1.0825088224469026e-05) < 1e-12
p, lo, hi = c.wilson(5, 10)
assert abs(lo - 0.2366) < 1e-3 and abs(hi - 0.7634) < 1e-3
print("rule fixtures:", len(cases) - bad, "/", len(cases), "pass")
sys.exit(1 if bad else 0)
