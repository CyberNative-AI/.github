"""Play listing presence: 200 ON_PLAY / 404 NOT_PLAY; >=1.2 s spacing; resumable jsonl."""
import json, sys, time, urllib.request, urllib.error, os
frame = json.load(open(sys.argv[1])); out = sys.argv[2]
done = {json.loads(l)["pkg"] for l in open(out)} if os.path.exists(out) else set()
UA = "Mozilla/5.0 (X11; Linux x86_64) cybernative-research/1.0 (+hello@cybernative.ai)"
def probe(pkg):
    url = f"https://play.google.com/store/apps/details?id={pkg}&hl=en&gl=US"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e: return e.code
    except Exception as e: return "ERR:" + type(e).__name__
with open(out, "a") as f:
    for r in frame:
        if r["pkg"] in done: continue
        c = probe(r["pkg"]); time.sleep(1.2)
        if c not in (200, 404):
            time.sleep(5); c2 = probe(r["pkg"]); time.sleep(1.2); c = c2 if c2 in (200, 404) else f"{c}|{c2}"
        cls = "ON_PLAY" if c == 200 else "NOT_PLAY" if c == 404 else "PLAY_UNKNOWN"
        f.write(json.dumps({"pkg": r["pkg"], "http": c, "play": cls}) + "\n"); f.flush()
