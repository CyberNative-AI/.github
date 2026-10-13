"""Build the sample: GitHub repositories of the top hex.pm packages by recent downloads.

usage: python3 fetch_list.py [N]   (default 500; anonymous hex.pm API, 100 packages per page)
Writes repos.tsv: package <TAB> owner/repo (lowercased), one line per package with a GitHub link.
A package's repository is its `GitHub`/`Source`/`Repository` link, else the first github.com link.
"""
import json, re, sys, time, urllib.request

N = int(sys.argv[1]) if len(sys.argv) > 1 else 500
PREFERRED = ("github", "source", "repository", "source code")


def repo(pkg):
    links = (pkg.get("meta") or {}).get("links") or {}
    for _, url in sorted(links.items(), key=lambda kv: (kv[0].lower() not in PREFERRED, kv[0])):
        m = re.match(r"https?://(?:www\.)?github\.com/([^/\s]+)/([^/\s#?]+)", str(url))
        if m:
            return f"{m.group(1)}/{m.group(2).removesuffix('.git')}".lower()
    return None


rows = []
for page in range(1, (N + 99) // 100 + 1):
    url = f"https://hex.pm/api/packages?sort=recent_downloads&page={page}"
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "checkbeam2604-sample"})
    with urllib.request.urlopen(req, timeout=60) as r:
        rows += json.load(r)
    time.sleep(1)
rows = rows[:N]
with open("repos.tsv", "w") as f:
    f.write(f"# fetched {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, top {N} by recent downloads\n")
    for p in rows:
        r = repo(p)
        if r:
            f.write(f"{p['name']}\t{r}\n")
repos = {line.split("\t")[1].strip() for line in open("repos.tsv") if not line.startswith("#")}
print(f"{len(rows)} packages, {len(repos)} distinct GitHub repositories")
