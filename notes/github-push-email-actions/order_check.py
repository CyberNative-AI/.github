#!/usr/bin/env python3
"""Compare the commit order in archived GitHub push emails with `git rev-list --reverse`.

usage: order_check.py <mbox> <git clone>   (uses each email's Compare range)
"""
import mailbox
import re
import subprocess
import sys
mbox,clone=sys.argv[1:3]
same=diff=skip=0
for i,m in enumerate(mailbox.mbox(mbox)):
    b=m.get_payload(decode=True).decode(m.get_content_charset() or "utf-8")
    ids=re.findall(r"^  Commit: ([0-9a-f]{40})",b,re.M)
    c=re.search(r"^Compare: \S+/compare/([0-9a-f]+)\.\.\.([0-9a-f]+)$",b,re.M)
    if not c: skip+=1; continue
    r=subprocess.run(["git","-C",clone,"rev-list","--reverse",f"{c[1]}..{c[2]}"],capture_output=True,text=True)
    got=r.stdout.split()
    if r.returncode: print(i,"rev-list failed",r.stderr.strip()[:80]); skip+=1; continue
    if got==ids: same+=1
    elif sorted(got)==sorted(ids): diff+=1; print(i,"same set, different order")
    else: diff+=1; print(i,f"different set: email {len(ids)} rev-list {len(got)}")
print(f"{same} same order, {diff} different, {skip} skipped (single commit or no Compare)")
