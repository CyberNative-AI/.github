#!/usr/bin/env python3
"""bot_logins.py - which bots opened the same-repo bot PRs counted by fork_share.py.

  python3 bot_logins.py run.tsv
Reads the repositories listed in a fork_share.py output file and, with the same window
and classification, counts merged PRs opened by bots from branches in the repository
itself (Dependabot excluded). AI Scan can run on these PRs.
"""
import collections, os, sys
from datetime import datetime, timedelta, timezone
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fork_share import get

cut = datetime.now(timezone.utc) - timedelta(days=90)
tot = collections.Counter()
for line in open(sys.argv[1]):
    f = line.rstrip("\n").split("\t")
    if f[0] in ("lang", "ALL") or len(f) < 4 or f[3] == "0": continue
    repo = f[1]; c = collections.Counter()
    for p in get(f"/repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=100"):
        if not p.get("merged_at") or datetime.fromisoformat(p["merged_at"].replace("Z", "+00:00")) < cut: continue
        head = (p.get("head") or {}).get("repo") or {}
        u = p["user"]
        if u["login"] == "dependabot[bot]" or head.get("id") != p["base"]["repo"]["id"]: continue
        if u["login"].endswith("[bot]") or u["type"] == "Bot": c[u["login"]] += 1
    if c: print(repo, dict(c)); tot.update(c)
print("ALL", dict(tot))
