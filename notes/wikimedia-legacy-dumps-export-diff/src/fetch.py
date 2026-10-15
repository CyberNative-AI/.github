"""Historical collection script (network). It documents how the evidence was collected; the supported
operation for this bundle is the offline recompute in RESULT.md. Its download and time limits are not enforced
(see the correction in PROTOCOL.md section 7): run it only under disk, memory and wall-time limits applied
outside the script.

Download the legacy and export files for one wiki and arm (resumable, sequential, checksum-verified).

usage: fetch.py WIKI {current,history}
Legacy files are verified against index.json sha1; export files against the export SHA256SUMS.
Abort clauses enforced here: HTTP 429 (Abort), 5 consecutive failed files (Abort),
cumulative download over DOWNLOAD_CAP_BYTES (Abort). A checksum mismatch is retried once,
then the wiki/arm is recorded UNUSABLE.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import time
import urllib.error
import urllib.request

from common import BULK, DOWNLOAD_CAP_BYTES, DUMPS, EVID, EXPORT_DATE, UA, Abort, http_get, read_json

LEDGER = EVID / "fetch-ledger.jsonl"
_fails = 0


def downloaded_total() -> int:
    if not LEDGER.exists():
        return 0
    return sum(json.loads(l).get("bytes", 0) for l in LEDGER.read_text().splitlines() if l.strip())


def log(rec: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")


def digest(path, algo: str) -> str:
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def get_file(url: str, dest, algo: str, want: str) -> bool:
    global _fails
    if dest.exists() and digest(dest, algo) == want:
        return True
    for attempt in (1, 2):
        if downloaded_total() > DOWNLOAD_CAP_BYTES:
            raise Abort("download cap exceeded")
        tmp = dest.with_suffix(dest.suffix + ".part")
        t0 = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
                shutil.copyfileobj(r, f, 1 << 20)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                raise Abort(f"HTTP 429 at {url}")
            log({"url": url, "error": f"HTTP {e.code}", "attempt": attempt, "bytes": 0})
            _fails += 1
            if _fails >= 5:
                raise Abort("5 consecutive failed files")
            continue
        except Exception as e:  # network errors count toward the consecutive-failure abort
            log({"url": url, "error": repr(e)[:200], "attempt": attempt, "bytes": 0})
            _fails += 1
            if _fails >= 5:
                raise Abort("5 consecutive failed files")
            time.sleep(10)
            continue
        size = tmp.stat().st_size
        ok = digest(tmp, algo) == want
        log({"url": url, "bytes": size, "secs": round(time.time() - t0, 1), "algo": algo, "ok": ok, "attempt": attempt})
        if ok:
            tmp.rename(dest)
            _fails = 0
            return True
        tmp.unlink()
    return False


def main(wiki: str, arm: str) -> int:
    frame = read_json(EVID / "frame.json")[wiki]
    out = BULK / arm / wiki
    (out / "legacy").mkdir(parents=True, exist_ok=True)
    (out / "export").mkdir(parents=True, exist_ok=True)
    status = {"wiki": wiki, "arm": arm, "legacy": [], "export": [], "unusable": []}
    files = frame["cur_files"] if arm == "current" else frame["hist_files"]
    for name, x in files.items():
        if not get_file(DUMPS + x["url"], out / "legacy" / name, "sha1", x["sha1"]):
            status["unusable"].append(name)
        status["legacy"].append(name)
    ds = "mediawiki_content_current" if arm == "current" else "mediawiki_content_history"
    base = f"{DUMPS}/other/{ds}/{wiki}/{EXPORT_DATE}/xml/bzip2/"
    try:
        sums = http_get(base + "SHA256SUMS").decode()
    except urllib.error.HTTPError as e:
        status["unusable"].append(f"SHA256SUMS HTTP {e.code}")
        sums = ""
    (out / "export" / "SHA256SUMS").write_text(sums)
    for line in sums.splitlines():
        h, name = line.split()
        name = name.lstrip("*./")
        if not get_file(base + name, out / "export" / name, "sha256", h):
            status["unusable"].append(name)
        status["export"].append(name)
    (out / "fetch-status.json").write_text(json.dumps(status, indent=1, sort_keys=True))
    print(json.dumps({"wiki": wiki, "arm": arm, "legacy": len(status["legacy"]), "export": len(status["export"]),
                      "unusable": status["unusable"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
