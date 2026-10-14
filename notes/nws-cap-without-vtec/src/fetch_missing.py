"""Fetch every alert id referenced (references or parameters.expiredReferences) by an Actual snapshot alert
but absent from the listing snapshot, so listing gaps are not scored as CAP failures. Raw bodies kept with sha256."""
import glob, hashlib, json, sys, time, urllib.error, urllib.request
from pathlib import Path

UA = "cybernative-research (https://cybernative.ai)"
raw = Path(sys.argv[1]); out = raw / "extra"; out.mkdir(exist_ok=True)
have, refs = set(), set()
for p in sorted(glob.glob(str(raw / "page-*.json"))):
    for f in json.loads(Path(p).read_text(encoding="utf-8"))["features"]:
        pr = f["properties"]; have.add(pr["id"])
        if pr.get("status") != "Actual":
            continue
        refs |= {r["identifier"] for r in pr.get("references") or []}
        for s in (pr.get("parameters") or {}).get("expiredReferences") or []:
            refs |= {t.split(",")[1] for t in s.split() if t.count(",") >= 2}
missing = sorted(refs - have)
print("missing", len(missing), flush=True)
log = []
def body_status(b):
    try:
        d = json.loads(b)
    except ValueError:
        return None
    return 200 if "properties" in d else d.get("status")

for i, rid in enumerate(missing):
    url = f"https://api.weather.gov/alerts/{rid}"
    fn = out / (rid.replace(":", "_") + ".json")
    if fn.exists() and body_status(fn.read_bytes()) in (200, 404):  # resume: keep earlier definitive answers
        b = fn.read_bytes()
        log.append({"id": rid, "status": body_status(b), "sha256": hashlib.sha256(b).hexdigest(), "resumed": True})
        continue
    status, body = None, b""
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/geo+json"}), timeout=60) as r:
                status, body = r.status, r.read(); break
        except urllib.error.HTTPError as e:
            status, body = e.code, e.read()
            if e.code == 404: break
        except Exception as e:
            status = repr(e)
        time.sleep(3 * (attempt + 1))
    fn.write_bytes(body)
    log.append({"id": rid, "status": status, "sha256": hashlib.sha256(body).hexdigest()})
    if i % 50 == 0: print(i, status, flush=True)
    time.sleep(0.5)
(raw / "extra-log.json").write_text(json.dumps(log, indent=1) + "\n")
import collections; print(collections.Counter(str(x["status"]) for x in log))
