#!/usr/bin/env python3
"""Check push_email.render() against real GitHub push emails from a list mbox.

usage: corpus_check.py <mbox> <bare-or-full git clone of the repo> <owner/repo>

For each archived email, the commit IDs and their order are read from the email
itself (the Actions payload supplies them in a live run); author, message,
committer date and changed paths come from the clone. The rendered body is
compared byte for byte with the email body up to its unsubscribe footer, and
the rendered subject with the subject minus the list's [tag] prefix.
"""
import mailbox
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import push_email  # noqa: E402

mbox_path, clone, repo = sys.argv[1:4]
mbox_path = os.path.abspath(mbox_path)
os.chdir(clone)


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


ok = bad = skipped = blocks = 0
for i, m in enumerate(mailbox.mbox(mbox_path)):
    real = m.get_payload(decode=True).decode(m.get_content_charset() or "utf-8")
    real_body = real.split("\nTo unsubscribe from these emails")[0]
    ids = re.findall(r"^  Commit: ([0-9a-f]{40})", real, re.M)
    if not ids:
        skipped += 1
        print(f"{i:3} SKIP no commits (ref moved without new commits)")
        continue
    if not all(push_email.have_commit(s) for s in ids):
        skipped += 1
        print(f"{i:3} SKIP commits not in clone")
        continue
    ref = re.search(r"^  Branch: (\S+)", real, re.M).group(1)
    cmp_ = re.search(r"Compare: \S+/compare/([0-9a-f]+)\.\.\.([0-9a-f]+)", real)
    before, after = (cmp_.groups() if cmp_ else ("0" * 12, ids[-1]))
    commits = []
    for s in ids:
        name, mail = git("log", "-1", "--format=%an%x00%ae", s).rstrip("\n").split("\x00")
        commits.append({"id": s, "message": git("log", "-1", "--format=%B", s),
                        "author": {"name": name, "email": mail}})
    event = {"ref": ref, "before": before, "after": after, "commits": commits}
    subject, body = push_email.render(event, repo)
    real_subject = re.sub(r"^\[[^\]]+\] (?=\[)", "", str(m["Subject"]).replace("\n", ""))
    blocks += len(ids)
    if body == real_body and subject == real_subject:
        ok += 1
        print(f"{i:3} MATCH {len(ids):3} commits {ref}")
    else:
        bad += 1
        a, b = real_body.splitlines(), body.splitlines()
        n = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
        print(f"{i:3} DIFF  {len(ids):3} commits {ref} subject_ok={subject == real_subject} "
              f"line {n}: real={a[n] if n < len(a) else None!r} ours={b[n] if n < len(b) else None!r}")
print(f"\n{ok} byte-identical, {bad} different, {skipped} skipped; {blocks} commit blocks checked")
