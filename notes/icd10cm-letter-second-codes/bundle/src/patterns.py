"""Descriptive arm: public ICD-10 format patterns applied to every probe code (dotted form)."""
import json, re, sys
# johndcook.com/blog/2019/05/05/regex_icd_codes/ (published unanchored for free-text search; anchored here for validation use)
# regex101.com/library/EOGAAH (Richard Baxter, 2024-06-05, verbatim incl. anchors); CMS edit -4036 is our encoding of its prose rule.
P = {"johndcook-2019": r"^[A-TV-Z][0-9][0-9AB]\.?[0-9A-TV-Z]{0,4}$",
     "regex101-EOGAAH": r"^[a-zA-Z]\d[a-zA-Z\d]\.?([a-zA-Z\d]{0,4})?$",
     "cms-edit-4036-rule": r"^[A-Za-z][0-9A-Za-z][0-9A-Za-z](\.[0-9A-Za-z]{0,4})?$"}
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
out = {k: {} for k in P}
for k, p in P.items():
    for r in rows:
        a = out[k].setdefault(r["arm"], [0, 0]); a[1] += 1; a[0] += bool(re.match(p, r["dotted"]))
print(json.dumps({"patterns": P, "accepted_of_n": out}, indent=1))
