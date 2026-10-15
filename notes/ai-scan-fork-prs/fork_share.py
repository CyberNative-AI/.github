#!/usr/bin/env python3
"""fork_share.py - share of a public repo's recently merged PRs that GitHub's AI Scan
for pull requests would skip (fork PRs and Dependabot PRs, per GitHub's docs).

  python3 fork_share.py owner/repo [owner/repo ...]          # one line per repo
  python3 fork_share.py --top HCL PHP Shell Dockerfile --n 10  # top-starred repos per language
Reads the public REST API anonymously (60 requests/hour); set GITHUB_TOKEN to raise that.
The token is sent only to https://api.github.com: a redirect to any other origin is refused.
fork_by_member: fork PRs whose author_association is OWNER, MEMBER or COLLABORATOR
(a lower bound: private org membership can show as CONTRIBUTOR to an outside reader).
Window: merged PRs among the 100 most recently updated closed PRs, merged in the last DAYS days.
"""
import argparse, json, os, sys, urllib.error, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone

API = "https://api.github.com"
KINDS = ("fork", "dependabot", "same_repo_bot", "same_repo")  # every merged PR is exactly one of these
class APIOnly(urllib.request.HTTPRedirectHandler):  # every hop must keep API's scheme and host
    def redirect_request(self, req, fp, code, msg, hdrs, newurl):
        if urllib.parse.urlsplit(newurl)[:2] != urllib.parse.urlsplit(API)[:2]:
            raise urllib.error.HTTPError(newurl, code, f"redirect away from {API} refused", hdrs, fp)
        return super().redirect_request(req, fp, code, msg, hdrs, newurl)

def get(path):
    h = {"Accept": "application/vnd.github+json", "User-Agent": "fork-share-check"}
    if os.environ.get("GITHUB_TOKEN"): h["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    with urllib.request.build_opener(APIOnly).open(urllib.request.Request(API + path, headers=h), timeout=30) as r:
        return json.load(r)

def top(lang, n):
    since = (datetime.now(timezone.utc) - timedelta(days=30)).date().isoformat()
    q = urllib.parse.quote(f"language:{lang} pushed:>={since} archived:false")
    return [(lang, i["full_name"], i["owner"]["type"]) for i in get(f"/search/repositories?q={q}&sort=stars&order=desc&per_page={n}")["items"]]

def measure(repo, days):
    cut = datetime.now(timezone.utc) - timedelta(days=days)
    pulls = get(f"/repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=100")
    c = {"fork": 0, "dependabot": 0, "same_repo": 0, "same_repo_bot": 0, "fork_by_member": 0}
    for p in pulls:
        if not p.get("merged_at") or datetime.fromisoformat(p["merged_at"].replace("Z", "+00:00")) < cut: continue
        head = (p.get("head") or {}).get("repo") or {}
        if p["user"]["login"] == "dependabot[bot]": c["dependabot"] += 1
        elif head.get("id") != p["base"]["repo"]["id"]:   # deleted fork -> head.repo null -> counts as fork
            c["fork"] += 1
            if p.get("author_association") in ("OWNER", "MEMBER", "COLLABORATOR"): c["fork_by_member"] += 1
        elif p["user"]["login"].endswith("[bot]") or p["user"]["type"] == "Bot": c["same_repo_bot"] += 1
        else: c["same_repo"] += 1
    return c

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("repos", nargs="*"); ap.add_argument("--top", nargs="*")
    ap.add_argument("--n", type=int, default=10); ap.add_argument("--days", type=int, default=90); a = ap.parse_args()
    rows = [("-", r, "?") for r in a.repos]
    for lang in a.top or []: rows += top(lang, a.n)
    print("lang\trepo\towner_type\tmerged\tfork\tdependabot\tsame_repo_bot\tsame_repo_human\tskipped_pct\tfork_by_member")
    tot = {"fork": 0, "dependabot": 0, "same_repo": 0, "same_repo_bot": 0, "fork_by_member": 0}
    for lang, repo, otype in rows:
        try: c = measure(repo, a.days)
        except Exception as e: print(f"{lang}\t{repo}\t{otype}\tERR {e}"); continue
        m = sum(c[k] for k in KINDS); s = c["fork"] + c["dependabot"]
        for k in tot: tot[k] += c[k]
        print(f"{lang}\t{repo}\t{otype}\t{m}\t{c['fork']}\t{c['dependabot']}\t{c['same_repo_bot']}\t{c['same_repo']}\t{(100*s/m if m else 0):.0f}\t{c['fork_by_member']}")
    m = sum(tot[k] for k in KINDS); s = tot["fork"] + tot["dependabot"]
    print(f"ALL\t-\t-\t{m}\t{tot['fork']}\t{tot['dependabot']}\t{tot['same_repo_bot']}\t{tot['same_repo']}\t{(100*s/m if m else 0):.0f}\t{tot['fork_by_member']}")
