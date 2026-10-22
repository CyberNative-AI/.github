"""Score Arm S outputs per frozen protocol. Usage: score.py OUTDIR > score.json"""
import json, pathlib, sys
MAL = {"MAL-2026-2144", "PYSEC-2026-2", "GHSA-5mg7-485q-xm76", "GHSA-92x9-889m-jgmw"}
O = pathlib.Path(sys.argv[1])

def ids_trivy(d):
    out, seen = [], False
    for r in d.get("Results") or []:
        for v in r.get("Vulnerabilities") or []:
            if v.get("PkgName", "").lower() == "litellm":
                out.append({v.get("VulnerabilityID")} | set(v.get("VendorIDs") or []))
    return out

def ids_grype(d):
    out = []
    for m in d.get("matches") or []:
        if m["artifact"]["name"].lower() == "litellm":
            s = {m["vulnerability"]["id"]} | {x["id"] for x in m.get("relatedVulnerabilities") or []}
            out.append(s)
    return out

def ids_osv(d):
    out = []
    for r in d.get("results") or []:
        for p in r.get("packages") or []:
            if p["package"]["name"].lower() == "litellm":
                for v in p.get("vulnerabilities") or []:
                    out.append({v["id"]} | set(v.get("aliases") or []))
    return out

def ids_pa(d):
    out, skip = [], None
    for dep in d.get("dependencies") or []:
        if dep.get("name", "").lower() == "litellm":
            if dep.get("skip_reason"):
                skip = dep["skip_reason"]
            for v in dep.get("vulns") or []:
                out.append({v["id"]} | set(v.get("aliases") or []))
    return out, skip

rows = []
for rc in sorted(O.glob("*.rc")):
    tool, V, F = rc.stem.rsplit("-", 2)
    code = int(rc.read_text().strip() or -1)
    raw = (O / f"{rc.stem}.json").read_text()
    err = (O / f"{rc.stem}.err").read_text()
    skip = None
    try:
        d = json.loads(raw) if raw.strip() else None
    except json.JSONDecodeError:
        d = None
    if d is None:
        outcome, ids = "ERROR", []
    else:
        if tool == "trivy": ids = ids_trivy(d)
        elif tool == "grype": ids = ids_grype(d)
        elif tool == "osv": ids = ids_osv(d)
        else: ids, skip = ids_pa(d)
        allids = set().union(*ids) if ids else set()
        if allids & MAL: outcome = "FLAG_MAL"
        elif ids: outcome = "FLAG_OTHER"
        elif skip: outcome = "SKIP"
        else: outcome = "CLEAN"
    rows.append({"tool": tool, "V": V, "F": F, "rc": code, "outcome": outcome,
                 "n_findings": len(ids), "mal_ids": sorted(set().union(*ids) & MAL) if ids else [],
                 "skip": skip, "err_tail": err.strip().splitlines()[-1][:200] if err.strip() else ""})
print(json.dumps(rows, indent=1))
