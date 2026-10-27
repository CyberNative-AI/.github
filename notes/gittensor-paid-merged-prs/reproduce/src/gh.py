"""Minimal GitHub REST GET. Uses GITHUB_TOKEN from the environment when set, otherwise anonymous (lower search rate limit)."""
import json, os, sys, time, urllib.request, urllib.error
UA = "cybernative-research-reproduce/1.0 (+hello@cybernative.ai)"
def headers(accept, auth=True):
    h = {"User-Agent": UA, "Accept": accept, "X-GitHub-Api-Version": "2022-11-28"}
    tok = os.environ.get("GITHUB_TOKEN")
    if auth and tok:
        h["Authorization"] = f"Bearer {tok}"
    return h
def get(path, accept="application/vnd.github+json", tries=3):
    url = path if path.startswith("http") else "https://api.github.com" + path
    for i in range(tries):
        req = urllib.request.Request(url, headers=headers(accept))
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode()), dict(r.headers)
        except urllib.error.HTTPError as e:
            h = e.headers or {}
            if e.code == 403:
                body = e.read().decode("utf-8", "replace")
                if "IP allow list" in body:  # some orgs refuse tokens from outside their allow list; public data reads anonymously
                    try:
                        with urllib.request.urlopen(urllib.request.Request(url, headers=headers(accept, auth=False)), timeout=40) as r:
                            return json.loads(r.read().decode()), dict(r.headers)
                    except urllib.error.HTTPError as e2:
                        return {"_error": e2.code, "_anon": True}, {}
            if e.code in (403, 429) and (h.get("X-RateLimit-Remaining") == "0" or h.get("Retry-After")):
                wait = int(h.get("Retry-After") or 0) or int(h.get("X-RateLimit-Reset") or 0) - time.time()
                if 0 < wait <= 90:
                    time.sleep(wait + 2); continue
                raise SystemExit(f"rate limit, wait {wait:.0f}s too long")
            if e.code in (502, 503) and i < tries - 1:
                time.sleep(5); continue
            return {"_error": e.code}, {}
    return {"_error": "tries"}, {}
if __name__ == "__main__":
    d, h = get(sys.argv[1])
    print(json.dumps(d, indent=1)[:int(sys.argv[2]) if len(sys.argv) > 2 else 4000])
