"""Compare checkbeam2604.py's version matching with setup-beam's own (expected.jsonl, from oracle.mjs).

usage: python3 tests/parity/compare.py [expected.jsonl]
Both sides resolve every spec on both builds.txt lists in tests/data. An "ERROR ..." result (the
action throws) matches any other error. A spec this port declines (UNKNOWN in the checker) is
counted, not compared. Exit status 1 on any difference.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
sys.dont_write_bytecode = True
import checkbeam2604 as c  # noqa: E402

DATA = os.path.join(HERE, "..", "data")
listing = {}
for osv in c.OSES:
    with open(os.path.join(DATA, f"otp-builds-ubuntu-{osv}.txt")) as f:
        listing[osv] = c.parse_listing(f.read())


def mine(spec, strict, osv):
    try:
        return c.version_from_spec(c.remove_otp(spec), listing[osv], strict)
    except c.ActionError:
        return "ERROR"
    except ValueError:
        return "DECLINED"


def norm(v):
    return "ERROR" if isinstance(v, str) and v.startswith("ERROR") else v


path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "expected.jsonl")
n = same = declined = 0
diffs = []
with open(path) as f:
    for line in f:
        e = json.loads(line)
        for osv in c.OSES:
            n += 1
            got = mine(e["spec"], e["strict"], osv)
            if got == "DECLINED":
                declined += 1
            elif got == norm(e[osv]):
                same += 1
            else:
                diffs.append((e["spec"], e["strict"], osv, e[osv], got))
for d in diffs[:40]:
    print("DIFF spec=%r strict=%s %s: setup-beam %r, port %r" % d)
print(f"{n} spec/strict/image cases: {same} same, {len(diffs)} different, {declined} declined (UNKNOWN)")
sys.exit(1 if diffs else 0)
