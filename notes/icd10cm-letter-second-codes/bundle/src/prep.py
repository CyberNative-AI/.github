"""Build the frozen probe arms for this study from CDC/NCHS ICD-10-CM code files (seed 13826)."""
import json, random, re, sys, xml.etree.ElementTree as ET
from pathlib import Path

X = Path(sys.argv[1])  # directory with the extracted CDC zips (inputs/SOURCES.md)
OUT = Path(sys.argv[2])

def load(p):
    return {l[:7].strip(): l[8:].strip() for l in p.read_text(encoding="latin-1").splitlines() if l.strip()}

fy25 = load(X / "fy25-desc/icd10cm-codes-2025.txt")
fy26 = load(X / "fy26-desc/icd10cm-codes-2026.txt")
fy27 = load(X / "icd10cm-code-descriptions-2027/icd10cm-code-descriptions-2027/icd10cm-codes-2027.txt")
apr = {n.text.replace(".", "") for n in ET.parse(X / "apr26-xml/icd10c-tabular-April-1-2026.xml").iter("name")}
apr_added = sorted(c for c in fy27 if c not in fy26 and c in apr)

def dotted(c):
    return c if len(c) <= 3 else c[:3] + "." + c[3:]

qa = lambda c: bool(re.match(r"^[A-Z][A-Z]", c))
rng = random.Random(13826)
arms = {
    "QA26": sorted(c for c in fy26 if qa(c) and c not in fy25),
    "QA27": sorted(c for c in fy27 if qa(c) and c not in fy26 and c not in apr_added),
    "N26": sorted(rng.sample(sorted(c for c in fy26 if c not in fy25 and not qa(c)), 13)),
    "N27": sorted(rng.sample(sorted(c for c in fy27 if c not in fy26 and c not in apr_added and not qa(c)), 13)),
    "OLD": sorted(rng.sample(sorted(c for c in fy27 if c in fy25 and c in fy26 and not qa(c)), 13)),
    "DEL27": sorted(rng.sample(sorted(c for c in fy26 if c not in fy27), 13)),
}
# M26: one FY2026-new non-QA code per QA26 code, same length and same last-character class (digit vs letter),
# so a tool's length/7th-character coverage gaps cannot masquerade as a letter-second format defect.
shape = lambda c: (len(c), c[-1].isdigit())
pool = sorted(c for c in fy26 if c not in fy25 and not qa(c))
m26 = []
for q in arms["QA26"]:
    cand = [c for c in pool if shape(c) == shape(q) and c not in m26]
    m26.append(rng.choice(cand))
arms["M26"] = sorted(m26)
desc = {**fy25, **fy26, **fy27}
rows = []
for arm, codes in arms.items():
    for c in codes:
        rows.append({"arm": arm, "code": c, "dotted": dotted(c), "desc": desc[c]})
for j in ["XYZ", "12345", "A0", "QA", "Q99.99999"]:
    rows.append({"arm": "JUNK", "code": j.replace(".", ""), "dotted": j, "desc": ""})
OUT.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
meta = {"n": {a: len(v) for a, v in arms.items()}, "fy25": len(fy25), "fy26": len(fy26), "fy27": len(fy27),
        "apr26_added_billable": apr_added, "qa_in_fy27": sorted(c for c in fy27 if qa(c))}
print(json.dumps(meta, indent=1))
