#!/usr/bin/env python3
"""summarize.py results.jsonl : counts and top actions for the note."""
import collections, json, re, sys

rows = [json.loads(l) for l in open(sys.argv[1])]
SHA = re.compile(r"@[0-9a-f]{40}$")
SILENT = {"action-image-tag", "action-dockerfile", "composite-docker-tag"}


def name(via):
    return via.rsplit("@", 1)[0]


wf = [r for r in rows if r["workflows"]]
remote = [r for r in wf if r["remote_uses"]]
print(f"repos scanned {len(rows)}; with workflows {len(wf)}; with >=1 remote action {len(remote)}")
kinds = collections.Counter()
for r in wf:
    for k in {f["kind"] for f in r["findings"]}:
        kinds[k] += 1
for k, n in kinds.most_common():
    print(f"  {k:22s} {n:5d} repos  {100*n/len(wf):5.1f}% of repos with workflows")
silent = [r for r in wf if any(f["kind"] in SILENT for f in r["findings"])]
print(f"  {'ANY silent image':22s} {len(silent):5d} repos  {100*len(silent)/len(wf):5.1f}%")
prebuilt = [r for r in wf if any(f["kind"] in ("action-image-tag", "composite-docker-tag") for f in r["findings"])]
print(f"  {'prebuilt image by tag':22s} {len(prebuilt):5d} repos  {100*len(prebuilt)/len(wf):5.1f}%")
shapinned = [r for r in wf if any(f["kind"] in SILENT and SHA.search(f["via"]) for f in r["findings"])]
print(f"  {'silent via SHA-pinned':22s} {len(shapinned):5d} repos")

for kind in ("action-image-tag", "action-dockerfile", "composite-docker-tag", "composite-local-path"):
    c, img = collections.Counter(), {}
    for r in wf:
        for a in {name(f["via"]) for f in r["findings"] if f["kind"] == kind}:
            c[a] += 1
        for f in r["findings"]:
            if f["kind"] == kind:
                img.setdefault(name(f["via"]), f.get("image") or f.get("base") or f.get("path"))
    print(f"\n{kind}: {len(c)} distinct actions")
    for a, n in c.most_common(15):
        print(f"  {n:4d}  {a}  {img[a]}")
