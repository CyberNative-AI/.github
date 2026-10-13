"""Merge per-container result dirs into one analysis dir (copies cells + tap logs, probes, client_era)."""
import os, shutil, sys
dst = sys.argv[1]; srcs = sys.argv[2:]
os.makedirs(os.path.join(dst, "tap"), exist_ok=True)
with open(os.path.join(dst, "cells.jsonl"), "w", encoding="utf-8") as out:
    for s in srcs:
        p = os.path.join(s, "cells.jsonl")
        if os.path.exists(p):
            out.write(open(p, encoding="utf-8").read())
        td = os.path.join(s, "tap")
        if os.path.isdir(td):
            for f in os.listdir(td):
                shutil.copy2(os.path.join(td, f), os.path.join(dst, "tap", f))
