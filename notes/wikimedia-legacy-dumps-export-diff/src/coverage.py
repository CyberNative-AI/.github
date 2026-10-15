"""Historical collection script (network). It documents how the evidence was collected; the supported
operation for this bundle is the offline recompute in RESULT.md. Its download and time limits are not enforced
(see the correction in PROTOCOL.md section 7): run it only under disk, memory and wall-time limits applied
outside the script.

Amendment 01 (post hoc, descriptive; not part of the verdict): for every frame wiki that has a
mediawiki_content_current directory, does the 2026-10-01 edition exist (SHA256SUMS present) for the
current and the history export? Resumable JSONL at evidence/coverage-editions.jsonl.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from common import DUMPS, EVID, EXPORT_DATE, UA, Abort, read_json

OUT = EVID / "coverage-editions.jsonl"


def head(url: str) -> int:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise Abort("HTTP 429")
        return e.code


def main() -> int:
    frame = read_json(EVID / "frame.json")
    done = set()
    if OUT.exists():
        done = {json.loads(l)["wiki"] for l in OUT.read_text().splitlines() if l.strip()}
    with OUT.open("a", encoding="utf-8") as f:
        for w in sorted(frame):
            if w in done or not frame[w]["in_export_current"]:
                continue
            rec = {"wiki": w, "sitematrix": frame[w]["sitematrix"], "cur_size": frame[w]["cur_size"]}
            for ds in ("mediawiki_content_current", "mediawiki_content_history"):
                rec[ds] = head(f"{DUMPS}/other/{ds}/{w}/{EXPORT_DATE}/xml/bzip2/SHA256SUMS")
                time.sleep(0.25)
            f.write(json.dumps(rec, sort_keys=True) + "\n")
            f.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
