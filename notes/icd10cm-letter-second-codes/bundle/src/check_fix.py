"""Apply the two public ICD-10 patterns and their position-2 edits to the 88 probe codes (dotted form).

Usage: python3 -I check_fix.py inputs/probes.jsonl
"""
import collections
import json
import re
import sys

PATTERNS = {
    "johndcook-2019": r"^[A-TV-Z][0-9][0-9AB]\.?[0-9A-TV-Z]{0,4}$",
    "johndcook-2019, position 2 edited": r"^[A-TV-Z][0-9A-Z][0-9AB]\.?[0-9A-TV-Z]{0,4}$",
    "regex101-EOGAAH": r"^[a-zA-Z]\d[a-zA-Z\d]\.?([a-zA-Z\d]{0,4})?$",
    "regex101-EOGAAH, position 2 edited": r"^[a-zA-Z][a-zA-Z\d][a-zA-Z\d]\.?([a-zA-Z\d]{0,4})?$",
}
ARMS = ["QA26", "QA27", "M26", "N26", "N27", "OLD", "DEL27", "JUNK"]

rows = [json.loads(line) for line in open(sys.argv[1], encoding="utf-8")]
for name, pattern in PATTERNS.items():
    counts = collections.defaultdict(lambda: [0, 0])
    accepted_junk = []
    for row in rows:
        code = row.get("dotted") or row["code"]
        ok = re.match(pattern, code) is not None
        counts[row["arm"]][0] += ok
        counts[row["arm"]][1] += 1
        if ok and row["arm"] == "JUNK":
            accepted_junk.append(code)
    print(name)
    print("  " + "  ".join(f"{arm} {counts[arm][0]}/{counts[arm][1]}" for arm in ARMS))
    if accepted_junk:
        print("  junk accepted: " + ", ".join(accepted_junk))
