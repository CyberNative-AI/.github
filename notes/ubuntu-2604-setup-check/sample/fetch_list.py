"""Build the repo sample from anonymous GitHub repository search (10 req/min). Writes repos.tsv."""
import json, time, urllib.parse, urllib.request
STRATA = [  # (name, query, sort, pages)
    ("py-mid", "language:Python stars:100..1000 pushed:>2026-09-12 archived:false fork:false", "updated", 3),
    ("py-top", "language:Python stars:>5000 pushed:>2026-09-12 archived:false fork:false", "stars", 2),
    ("rb-mid", "language:Ruby stars:50..1000 pushed:>2026-09-12 archived:false fork:false", "updated", 2),
    ("rb-top", "language:Ruby stars:>1000 pushed:>2026-09-12 archived:false fork:false", "stars", 1),
]
seen, rows = set(), []
for name, q, sort, pages in STRATA:
    for page in range(1, pages + 1):
        url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
            {"q": q, "sort": sort, "order": "desc", "per_page": 100, "page": page})
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "runner2604-check"})
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.load(r)
        for it in d["items"]:
            if it["full_name"] in seen:
                continue
            seen.add(it["full_name"])
            rows.append((name, it["full_name"], it["default_branch"], it["stargazers_count"], it["pushed_at"]))
        print(name, page, d["total_count"], len(d["items"]), flush=True)
        time.sleep(7)
with open("repos.tsv", "w") as f:
    f.write(f"# fetched {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
    for r in rows:
        f.write("\t".join(map(str, r)) + "\n")
print("repos", len(rows))
