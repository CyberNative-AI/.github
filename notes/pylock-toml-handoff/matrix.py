"""Group scored.json into label counts per target|producer|kind (NO_ORACLE excluded).

Usage: python3 -I matrix.py results/scored.json > results/matrix.json
"""
import collections
import json
import sys

counts = collections.defaultdict(collections.Counter)
for row in json.load(open(sys.argv[1], encoding="utf-8")):
    if row["label"] != "NO_ORACLE":
        counts[f"{row['target']}|{row['producer']}|{row['kind']}"][row["label"]] += 1
sys.stdout.write(json.dumps({k: dict(v) for k, v in counts.items()}, indent=1, sort_keys=True))
