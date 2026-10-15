"""Historical collection script (network). It documents how the evidence was collected; the supported
operation for this bundle is the offline recompute in RESULT.md. Its download and time limits are not enforced
(see the correction in PROTOCOL.md section 7): run it only under disk, memory and wall-time limits applied
outside the script.

Resumable driver: for each arm-wiki, fetch -> extract -> delete raw .bz2 (teardown). Then rcfetch and compare.

usage: run_all.py {rc,data,compare}
Each step is skipped when its output already exists. An Abort from fetch stops the whole run (exit 3).
Progress lines go to evidence/run-log.jsonl.
"""
from __future__ import annotations

import json
import sys
import time

import compare
import extract
import fetch
import rcfetch
from common import BULK, EVID, Abort, read_json

LOG = EVID / "run-log.jsonl"


def log(**kw) -> None:
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **kw}, sort_keys=True) + "\n")


def jobs() -> list[tuple[str, str]]:
    s = read_json(EVID / "sample.json")
    out = [(x["wiki"], "current") for x in s["sample"]] + [(w, "history") for w in s["history_arm"]]
    return out + [(w, "current") for w in s["targeted"]]


def main(step: str) -> int:
    js = jobs()
    if step == "rc":
        for w in sorted({w for w, _ in js}):
            if (EVID / "rc" / f"{w}.json").exists() or (EVID / "rc" / f"{w}.json.gz").exists():
                continue
            try:
                rcfetch.main(w)
                log(step="rc", wiki=w, ok=True)
            except Abort as e:
                log(step="rc", wiki=w, abort=str(e))
                return 3
            except Exception as e:
                log(step="rc", wiki=w, error=repr(e)[:300])
    elif step == "data":
        for w, arm in js:
            root = BULK / arm / w
            if (root / "extract-summary.json").exists():
                continue
            try:
                fetch.main(w, arm)
            except Abort as e:
                log(step="fetch", wiki=w, arm=arm, abort=str(e))
                return 3
            st = json.loads((root / "fetch-status.json").read_text())
            if st["unusable"]:
                log(step="fetch", wiki=w, arm=arm, unusable=st["unusable"])
                continue
            extract.main(w, arm, 4)
            for p in list((root / "legacy").glob("*.bz2")) + list((root / "export").glob("*.bz2")):
                p.unlink()
            log(step="data", wiki=w, arm=arm, ok=True, summary=json.loads((root / "extract-summary.json").read_text()))
    elif step == "compare":
        for w, arm in js:
            if not (BULK / arm / w / "extract-summary.json").exists() or (EVID / "compare" / arm / f"{w}.json").exists():
                continue
            try:
                compare.main(w, arm)
                log(step="compare", wiki=w, arm=arm, ok=True)
            except Abort as e:
                log(step="compare", wiki=w, arm=arm, abort=str(e))
                return 3
            except Exception as e:
                log(step="compare", wiki=w, arm=arm, error=repr(e)[:300])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
