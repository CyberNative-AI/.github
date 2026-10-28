"""Fetch: GitHub search slices, pulls/{n} sizes, timelines for closed items. Stdlib only.

Usage: python3 -I src/fetch.py OUTDIR [--read-time ISO]
Writes OUTDIR/raw/* (every API response), OUTDIR/raw/MANIFEST.tsv (sha256), OUTDIR/data/items.jsonl.
Set GITHUB_TOKEN to any token that can read public data; without it the script runs anonymously and slower.
"""
import datetime as dt
import hashlib
import http.client
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

REPO = "JuliaLang/julia"
F_AUTHORS = ("MilesCranmerBot", "MilesCranmer")
OUTSIDE = {"NONE", "FIRST_TIME_CONTRIBUTOR", "FIRST_TIMER", "CONTRIBUTOR", "MANNEQUIN"}
INSIDE = {"MEMBER", "OWNER", "COLLABORATOR"}
F_START = dt.datetime(2026, 10, 24, tzinfo=dt.timezone.utc)
PRIOR_START = dt.datetime(2026, 8, 1, tzinfo=dt.timezone.utc)
PRIOR_END = dt.datetime(2026, 10, 23, 23, 59, 59, tzinfo=dt.timezone.utc)
TIMELINE_H = 72  # hours: timeline reads for items closed within this age
MAX_CALLS = 1500


def load_token():
    return os.environ.get("GITHUB_TOKEN") or None


class Api:
    def __init__(self, out, token):
        self.out, self.token, self.calls = out, token, 0
        self.manifest = open(out / "raw" / "MANIFEST.tsv", "a", encoding="utf-8")

    def get(self, path, name, accept="application/vnd.github+json"):
        if self.calls >= MAX_CALLS:
            raise SystemExit(f"ABORT: call ceiling {MAX_CALLS}")
        url = "https://api.github.com" + path
        for attempt in range(4):
            req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "cybernative-research",
                                                       "X-GitHub-Api-Version": "2022-11-28"})
            if self.token:
                req.add_header("Authorization", "Bearer " + self.token)
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    body = r.read()
                    remaining = r.headers.get("X-RateLimit-Remaining")
                    reset = r.headers.get("X-RateLimit-Reset")
                break
            except urllib.error.HTTPError as e:
                if e.code in (403, 429) and attempt < 3:
                    wait = int(e.headers.get("Retry-After") or 0) or max(5, int(e.headers.get("X-RateLimit-Reset", time.time() + 30)) - int(time.time()) + 2)
                    print(f"rate limited on {name}; sleeping {min(wait, 120)} s", file=sys.stderr)
                    time.sleep(min(wait, 120))
                    continue
                raise
            except (http.client.IncompleteRead, urllib.error.URLError, TimeoutError, ConnectionError) as e:
                if attempt < 3:
                    print(f"transport error on {name}: {type(e).__name__}; retrying", file=sys.stderr)
                    time.sleep(5 * (attempt + 1))
                    continue
                raise
        self.calls += 1
        f = self.out / "raw" / (name + ".json")
        f.write_bytes(body)
        self.manifest.write(f"{f.name}\t{hashlib.sha256(body).hexdigest()}\t{url}\n")
        self.manifest.flush()
        if remaining is not None and int(remaining) < 3 and "search" in path:
            time.sleep(max(1, int(reset) - int(time.time()) + 2))
        return json.loads(body)


def iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def search(api, query, tag):
    items, page = [], 1
    while True:
        q = urllib.parse.quote(query, safe=":+")
        d = api.get(f"/search/issues?q={q}&per_page=100&page={page}", f"search-{tag}-p{page}")
        if d.get("total_count", 0) > 1000:
            raise SystemExit(f"ABORT: slice {tag} total_count {d['total_count']} > 1000")
        if d.get("incomplete_results"):
            d2 = api.get(f"/search/issues?q={q}&per_page=100&page={page}", f"search-{tag}-p{page}-retry")
            if d2.get("incomplete_results"):
                raise SystemExit(f"ABORT: incomplete_results twice for {tag}")
            d = d2
        items += d["items"]
        if len(d["items"]) < 100:
            return items, d["total_count"]
        page += 1
        time.sleep(2.5)


def group_of(it, read_time):
    login = it["user"]["login"]
    created = dt.datetime.fromisoformat(it["created_at"].replace("Z", "+00:00"))
    is_bot = it["user"].get("type") == "Bot" or login.endswith("[bot]")
    if login in F_AUTHORS:
        return "F" if created >= F_START else "F_before"
    if is_bot:
        return "bot"
    assoc = it["author_association"]
    if created >= F_START:
        return "O_same" if assoc in OUTSIDE else ("I_same" if assoc in INSIDE else "other")
    if PRIOR_START <= created <= PRIOR_END:
        return "O_prior" if assoc in OUTSIDE else ("I_prior" if assoc in INSIDE else "other")
    return "other"


def main():
    out = pathlib.Path(sys.argv[1])
    read_time = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    if "--read-time" in sys.argv:
        read_time = dt.datetime.fromisoformat(sys.argv[sys.argv.index("--read-time") + 1].replace("Z", "+00:00"))
    (out / "raw").mkdir(parents=True, exist_ok=True)
    (out / "data").mkdir(parents=True, exist_ok=True)
    token = load_token()
    api = Api(out, token)
    meta = {"read_time": iso(read_time), "token": "app-read" if token else "none"}
    print(json.dumps(meta))

    seen = {}
    slices = []
    # Batch window: everything created since F_START (all authors), daily slices.
    d = F_START
    while d <= read_time:
        e = min(d + dt.timedelta(days=1) - dt.timedelta(seconds=1), read_time)
        slices.append((f"created:{iso(d)}..{iso(e)}", f"w{d:%m%d}"))
        d += dt.timedelta(days=1)
    # Prior window: weekly slices split by type.
    d = PRIOR_START
    while d <= PRIOR_END:
        e = min(d + dt.timedelta(days=7) - dt.timedelta(seconds=1), PRIOR_END)
        for typ in ("pr", "issue"):
            slices.append((f"created:{iso(d)}..{iso(e)} is:{typ}", f"p{d:%m%d}-{typ}"))
        d += dt.timedelta(days=7)
    counts = {}
    for q, tag in slices:
        items, total = search(api, f"repo:{REPO} {q}", tag)
        counts[tag] = [total, len(items)]
        for it in items:
            seen[it["number"]] = it
        time.sleep(2.5)
    meta["slices"] = counts

    rows = []
    for n, it in sorted(seen.items()):
        g = group_of(it, read_time)
        if g in ("other", "bot", "F_before"):
            continue
        is_pr = bool(it.get("pull_request"))
        row = {"number": n, "group": g, "is_pr": is_pr, "login": it["user"]["login"],
               "assoc": it["author_association"], "created_at": it["created_at"], "closed_at": it["closed_at"],
               "state": it["state"], "state_reason": it.get("state_reason"),
               "merged_at": (it.get("pull_request") or {}).get("merged_at"), "draft": it.get("draft"),
               "title": it["title"], "comments": it["comments"], "labels": [l["name"] for l in it["labels"]]}
        rows.append(row)

    def age_at_close(r):
        if not r["closed_at"]:
            return None
        c = dt.datetime.fromisoformat(r["closed_at"].replace("Z", "+00:00"))
        s = dt.datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        return (c - s).total_seconds() / 3600

    for r in rows:
        if r["is_pr"] and r["group"] in ("F", "O_prior", "O_same"):
            p = api.get(f"/repos/{REPO}/pulls/{r['number']}", f"pull-{r['number']}")
            r.update({"additions": p["additions"], "deletions": p["deletions"], "changed_files": p["changed_files"],
                      "draft": p["draft"], "merged_by": (p.get("merged_by") or {}).get("login"),
                      "merged_at": p.get("merged_at")})
        a = age_at_close(r)
        needs_tl = r["group"] in ("F", "O_prior", "O_same") and a is not None and a <= TIMELINE_H and (
            (r["is_pr"] and not r["merged_at"]) or not r["is_pr"])
        if needs_tl:
            ev, page = [], 1
            while True:
                t = api.get(f"/repos/{REPO}/issues/{r['number']}/timeline?per_page=100&page={page}",
                            f"timeline-{r['number']}-p{page}")
                ev += t
                if len(t) < 100:
                    break
                page += 1
            r["closed_commit_ids"] = [x.get("commit_id") for x in ev if x.get("event") == "closed" and x.get("commit_id")]
            r["closers"] = [(x.get("actor") or {}).get("login") for x in ev if x.get("event") == "closed"]
            xr = []
            for x in ev:
                if x.get("event") != "cross-referenced":
                    continue
                src = (x.get("source") or {}).get("issue") or {}
                if not src.get("pull_request"):
                    continue
                if (src.get("repository") or {}).get("full_name") != REPO:
                    continue
                xr.append({"number": src["number"], "merged_at": src["pull_request"].get("merged_at"),
                           "login": (src.get("user") or {}).get("login")})
            r["xref_prs"] = xr
    with open(out / "data" / "items.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    meta["calls"] = api.calls
    meta["n_items"] = len(rows)
    (out / "data" / "fetch-meta.json").write_text(json.dumps(meta, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: meta[k] for k in ("read_time", "calls", "n_items")}))


if __name__ == "__main__":
    main()
