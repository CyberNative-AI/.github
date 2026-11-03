"""Re-read the note's 143 old-names-only repositories at their default branch (raw HEAD), Stable day.
Same text rules as the October 23 census: OLD = texElementImage2D|copyElementImageToTexture, NEW = census NEW_RE.
usage: python3 -I head_recheck_20261103.py <old-names-only.json> <out.jsonl>   (summary on stdout)"""
import json, re, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

OLD_RE = re.compile(r"texElementImage2D|copyElementImageToTexture")
NEW_RE = re.compile(r"texElementSubImage2D|drawElementImageToTexture|content\s*=\s*[\"']drawable[\"']|setAttribute\(\s*[\"']content[\"']")


def fetch(repo, path):
    url = f"https://raw.githubusercontent.com/{repo}/HEAD/{urllib.request.quote(path)}"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "cybernative-census-recheck"}), timeout=30) as r:
                t = r.read().decode("utf-8", "replace")
                return {"status": 200, "old": bool(OLD_RE.search(t)), "new": bool(NEW_RE.search(t))}
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"status": 404, "old": None, "new": None}
            err = f"HTTP {e.code}"
        except Exception as e:  # network
            err = type(e).__name__
        time.sleep(2 * (attempt + 1))
    return {"status": "error", "error": err, "old": None, "new": None}


def main(src, out):
    repos = json.load(open(src))["repos"]
    jobs = [(r["repo"], p) for r in repos for p in r["files"]]
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(lambda j: (j, fetch(*j), datetime.now(timezone.utc).isoformat(timespec="seconds")), jobs))
    with open(out, "w") as f:
        for (repo, path), r, at in res:
            f.write(json.dumps({"repo": repo, "path": path, "read_at": at, **r}, sort_keys=True) + "\n")
    by = {}
    for (repo, _), r, _ in res:
        by.setdefault(repo, []).append(r)
    cls = {}
    for repo, rs in by.items():
        if any(r["status"] == "error" for r in rs):
            c = "ERROR"
        elif any(r["new"] for r in rs):
            c = "HAS_NEW_NAMES"
        elif any(r["old"] for r in rs):
            c = "STILL_OLD_ONLY"
        elif all(r["status"] == 404 for r in rs):
            c = "FILES_GONE"
        else:
            c = "OLD_NAMES_REMOVED"
        cls[repo] = c
    counts = {}
    for c in cls.values():
        counts[c] = counts.get(c, 0) + 1
    print(json.dumps({"repos": len(cls), "files": len(jobs), "classes": dict(sorted(counts.items())),
                      "changed": sorted(r for r, c in cls.items() if c != "STILL_OLD_ONLY")}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:3])
