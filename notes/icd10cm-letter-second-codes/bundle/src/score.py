"""Scorer: per-tool arm counts, classification, ruling. Usage: score.py RUNDIR [RUNDIR2] > score.json"""
import json, sys
from pathlib import Path
MAINT = {"simple-icd-10-cm": "StefanoTrv", "icdlookup": "icdlookup", "cms-icd": "ipolharvard", "icd10-coder": "icd10-coder",
         "@lowlysre/icd-10-cm": "lowlysre", "icdwise": "icdwise", "@cyanheads/medical-codes-mcp-server": "cyanheads",
         "@easysolutions906/mcp-healthcare": "easysolutions906", "@cosyte/terminology": "cosyte",
         "nlm-clinicaltables": "NLM", "tx.fhir.org": "HL7"}
def load(d):
    out = {}
    for f in sorted(Path(d).rglob("*.jsonl")):
        rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
        out[rows[0]["tool"]] = {"rows": rows, "bytes": f.read_bytes()}
    return out
r1 = load(sys.argv[1]); r2 = load(sys.argv[2]) if len(sys.argv) > 2 else {}
res = {}
for tool, d in sorted(r1.items()):
    rows = d["rows"]
    if "setup_error" in rows[0]:
        res[tool] = {"excluded": "setup_error", "detail": rows[0]["setup_error"][-300:]}; continue
    arm = {}
    for r in rows:
        a = arm.setdefault(r["arm"], {"n": 0, "accept": 0, "errors": 0})
        a["n"] += 1; a["accept"] += r["accept"]; a["errors"] += r["error"] is not None
    err = sum(a["errors"] for a in arm.values()) / len(rows)
    acc = lambda k: arm.get(k, {}).get("accept", 0)
    if acc("M26") <= 2: cls = "STALE_PRE26"
    elif acc("M26") >= 10 and acc("QA26") <= 2: cls = "FORMAT_REJECT"
    elif acc("QA26") >= 12: cls = "QA_OK"
    else: cls = "OTHER"
    sec = "QA27_GAP" if acc("N27") >= 10 and acc("QA27") <= 1 else ("CURRENT27" if acc("N27") >= 12 and acc("QA27") >= 4 else "NOT_CURRENT27")
    g2 = None if tool not in r2 else (r2[tool]["bytes"] == d["bytes"])
    excl = "G3_errors" if err > 0.10 else ("G2_nondeterministic" if g2 is False and not tool.startswith(("nlm", "tx.")) else None)
    res[tool] = {"maintainer": MAINT.get(tool, tool), "call": rows[0]["call"], "arms": arm, "class": cls, "fy2027": sec,
                 "error_rate": round(err, 3), "rerun_identical": g2, "excluded": excl,
                 "qa_rows": [{k: r[k] for k in ("code", "arm", "accept", "raw", "error")} for r in rows if r["arm"] in ("QA26", "QA27")]}
hits = {t: v for t, v in res.items() if not v.get("excluded") and (v["class"] == "FORMAT_REJECT" or v["fy2027"] == "QA27_GAP")}
n_excl = sum(1 for v in res.values() if v.get("excluded"))
maint = {v["maintainer"] for v in hits.values()}
ruling = "INVALID" if n_excl > 4 else ("CONTINUE" if len(maint) >= 2 else ("CHANGE" if len(maint) == 1 else "STOP"))
print(json.dumps({"ruling": ruling, "hits": sorted(hits), "n_tools": len(res), "n_excluded": n_excl, "tools": res}, indent=1, sort_keys=True))
