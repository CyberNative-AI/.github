"""Free-service arm (network): NLM Clinical Tables ICD-10-CM API and tx.fhir.org $validate-code. Usage: services.py PROBES OUTDIR"""
import json, sys, time, urllib.parse, urllib.request
from pathlib import Path
probes = [json.loads(l) for l in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()]
out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
def get(url, accept="application/json"):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "cybernative-research/1.0 (hello@cybernative.ai)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))
def nlm(p):
    d = get("https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search?" + urllib.parse.urlencode({"sf": "code", "terms": p["dotted"], "maxList": 50}))
    return p["dotted"] in (d[1] or []), json.dumps(d[3][:2])
def tx(p):
    d = get("https://tx.fhir.org/r4/CodeSystem/$validate-code?" + urllib.parse.urlencode({"url": "http://hl7.org/fhir/sid/icd-10-cm", "code": p["dotted"]}), "application/fhir+json")
    prm = {x["name"]: next((v for k, v in x.items() if k.startswith("value")), None) for x in d.get("parameter", [])}
    return prm.get("result") is True, json.dumps({k: prm.get(k) for k in ("version", "display", "message")})
for name, call, fn in [("nlm-clinicaltables", "GET clinicaltables.nlm.nih.gov/api/icd10cm/v3/search sf=code terms=dotted; accept = exact dotted code in result list", nlm),
                       ("tx.fhir.org", "GET tx.fhir.org/r4/CodeSystem/$validate-code url=http://hl7.org/fhir/sid/icd-10-cm code=dotted; accept = result true", tx)]:
    rows = []
    for p in probes:
        try:
            ok, raw = fn(p); err = None
        except Exception as e:
            ok, raw, err = False, None, f"{type(e).__name__}: {str(e)[:200]}"
        rows.append({"tool": name, "call": call, "arm": p["arm"], "code": p["code"], "accept": bool(ok), "raw": raw and raw[:160], "error": err})
        time.sleep(0.5)
    (out / f"{name}.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    print(name, sum(r["accept"] for r in rows), "/", len(rows))
