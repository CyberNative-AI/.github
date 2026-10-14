"""Second run, fresh-window check: one pass over the live api.weather.gov /alerts listing, 1 req/s, URL-only User-Agent. Read-only."""
import hashlib, json, sys, time, urllib.request
from pathlib import Path
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
url, log, reqs = "https://api.weather.gov/alerts?limit=500", [], 0
while url:
    req = urllib.request.Request(url, headers={"User-Agent": "https://cybernative.ai", "Accept": "application/geo+json"})
    for attempt in range(2):
        reqs += 1
        try:
            body = urllib.request.urlopen(req, timeout=90).read(); break
        except Exception as e:
            print("retry", reqs, repr(e), flush=True); time.sleep(5)
    else: raise SystemExit("failed")
    d = json.loads(body); i = len(log)
    (out / f"page-{i:03d}.json").write_bytes(body)
    log.append({"page": i, "n": len(d["features"]), "sha256": hashlib.sha256(body).hexdigest(), "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    url = (d.get("pagination") or {}).get("next")
    if not d["features"]: break
    time.sleep(1)
(out / "fetch-log.json").write_text(json.dumps({"requests": reqs, "pages": log}, indent=1) + "\n"); print("requests", reqs, "pages", len(log))
