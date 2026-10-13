"""Frame: GitHub repo search (unauthenticated), per-day pushed windows, seeded random page.
Writes data/frame-<stratum>.jsonl. Deterministic given the seed and the API's answers (logged raw)."""
import json, random, sys, time, urllib.parse, urllib.request, pathlib, datetime
OUT = pathlib.Path(__file__).resolve().parent.parent / "data"
def get(q, page, sort=None):
    params = {"q": q, "per_page": 100, "page": page}
    if sort: params.update(sort=sort, order="desc")
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(params)
    for attempt in range(6):
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "research-frame"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (403, 429): time.sleep(65); continue
            raise
    raise SystemExit("rate limit loop")
def main(stratum):
    rows = []
    if stratum == "random":
        rnd = random.Random(13253)
        end = datetime.date(2026, 10, 11)
        for k in range(21):
            day = end - datetime.timedelta(days=k)
            q = f"stars:>=10 fork:false archived:false pushed:{day.isoformat()}"
            page = rnd.randint(1, 10)
            d = get(q, page)
            for it in d.get("items", []):
                rows.append({"repo": it["full_name"], "owner": it["owner"]["login"], "stars": it["stargazers_count"],
                             "pushed_at": it["pushed_at"], "default_branch": it["default_branch"], "q": q, "page": page,
                             "total": d.get("total_count")})
            print(day, page, d.get("total_count"), len(d.get("items", [])), file=sys.stderr)
            time.sleep(7)
    else:
        for page in (1, 2):
            d = get("stars:>=30000 fork:false archived:false pushed:>=2026-09-12", page, sort="stars")
            for it in d.get("items", []):
                rows.append({"repo": it["full_name"], "owner": it["owner"]["login"], "stars": it["stargazers_count"],
                             "pushed_at": it["pushed_at"], "default_branch": it["default_branch"], "page": page})
            time.sleep(7)
    (OUT / f"frame-{stratum}.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    print(stratum, len(rows), file=sys.stderr)
if __name__ == "__main__":
    main(sys.argv[1])
