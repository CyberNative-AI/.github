"""Fetch comments for the F hand-read set (closed F items + open F items with comments). Raw saved; prints a reading digest."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import fetch as fe
out = pathlib.Path(sys.argv[1])
rows = [json.loads(l) for l in open(out / "data" / "items.jsonl")]
api = fe.Api(out, fe.load_token())
sel = [r for r in rows if r["group"] == "F" and ((r["state"] == "closed" and not (r["is_pr"] and r.get("merged_at"))) or r["comments"] > 0)]
digest = []
for r in sel:
    cs = api.get(f"/repos/{fe.REPO}/issues/{r['number']}/comments?per_page=100", f"comments-{r['number']}")
    digest.append({"number": r["number"], "is_pr": r["is_pr"], "state": r["state"], "state_reason": r["state_reason"],
                   "merged_at": r.get("merged_at"), "closers": r.get("closers"), "closed_commit_ids": r.get("closed_commit_ids"),
                   "xref_prs": r.get("xref_prs"), "title": r["title"],
                   "comments": [(c["user"]["login"], c["author_association"], c["created_at"], c["body"]) for c in cs]})
(out / "data" / "handread-digest.json").write_text(json.dumps(digest, indent=1) + "\n")
print(len(sel), "items;", api.calls, "calls")
