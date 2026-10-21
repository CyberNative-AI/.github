"""Census frame from the F-Droid index-v2 file fetched on 2026-10-21."""
import json, sys, datetime as dt
idx = json.load(open(sys.argv[1]))
cut = dt.datetime(2025, 10, 21, tzinfo=dt.timezone.utc).timestamp() * 1000
rows = []
for pk, p in sorted(idx["packages"].items()):
    vs = sorted(p["versions"].values(), key=lambda x: x["manifest"]["versionCode"])
    if not vs: continue
    lv = vs[-1]; t = lv["manifest"].get("usesSdk", {}).get("targetSdkVersion")
    m = p["metadata"]; sc = (m.get("sourceCode") or "").strip().rstrip("/")
    host = sc.split("/")[2] if sc.count("/") >= 2 else ""
    if m.get("lastUpdated", 0) < cut or t is None or t > 35: continue
    if host not in ("github.com", "gitlab.com", "codeberg.org"): continue
    rows.append({"pkg": pk, "fdroid_target": t, "source": sc, "host": host,
                 "lastUpdated": dt.datetime.fromtimestamp(m["lastUpdated"]/1000, dt.timezone.utc).date().isoformat(),
                 "versionCode": lv["manifest"]["versionCode"]})
json.dump(rows, open(sys.argv[2], "w"), indent=0)
print(len(rows))
