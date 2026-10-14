"""Snapshot every alert currently listed by api.weather.gov /alerts (rolling ~7-day window).
Raw pages are written append-only with sha256; no outcome is computed here."""
import hashlib, json, sys, time, urllib.request
from pathlib import Path

UA = "cybernative-research (https://cybernative.ai)"
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
url = "https://api.weather.gov/alerts?limit=500"
log = []
for i in range(60):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/geo+json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                body = r.read(); break
        except Exception as e:  # transient 5xx are common on this API
            print("retry", i, attempt, repr(e), flush=True); time.sleep(5 * (attempt + 1))
    else:
        raise SystemExit(f"page {i} failed")
    p = out / f"page-{i:03d}.json"; p.write_bytes(body)
    d = json.loads(body); n = len(d["features"])
    log.append({"page": i, "url": url, "n": n, "sha256": hashlib.sha256(body).hexdigest(),
                "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    print(log[-1], flush=True)
    url = (d.get("pagination") or {}).get("next")
    if not n or not url: break
    time.sleep(1)
(out / "collect-log.json").write_text(json.dumps(log, indent=1) + "\n")
