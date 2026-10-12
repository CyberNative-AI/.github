"""Compare check2604's version-range matching with node-semver's answers in semver-oracle.json.

semver-oracle.json was produced with npm's bundled semver in the node:24 image:
  docker run --rm -v "$PWD/tests":/t node:24 node /t/oracle.js > tests/semver-oracle.json
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import check2604 as c  # noqa: E402

cases = json.load(open(os.path.join(HERE, "semver-cases.json")))
oracle = json.load(open(os.path.join(HERE, "semver-oracle.json")))
pairs = mismatches = 0
for r in cases["ranges"]:
    if oracle[r] == "ERR":  # node-semver rejects the range; not compared
        continue
    for v in cases["versions"]:
        pairs += 1
        if c.satisfies(v, r) != (v in oracle[r]):
            mismatches += 1
            print("mismatch", repr(v), repr(r))
print(f"{pairs} pairs, {mismatches} mismatches")
sys.exit(1 if mismatches else 0)
