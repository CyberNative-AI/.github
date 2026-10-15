"""Shared helpers (Wikimedia legacy dump vs Content File Export equivalence)."""
from __future__ import annotations

import gzip
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

UA = "cybernative-research-check (https://cybernative.ai)"
LAB = Path(__file__).resolve().parents[1]
INPUTS = LAB / "inputs"
EVID = LAB / "evidence"
BULK = Path(os.environ.get("DUMPS_WORK", LAB / "work"))  # raw dumps and extraction records (large)
DUMPS = "https://dumps.wikimedia.org"
LEGACY_DATE = "20261001"
EXPORT_DATE = "2026-10-01"
SEED = 13793
# Frozen snapshot window (UTC). Any page touched in W is timing-explainable.
W_START = "2026-09-28T00:00:00Z"
W_END = "2026-10-08T00:00:00Z"
DOWNLOAD_CAP_BYTES = 25 * 10**9


class Abort(RuntimeError):
    """A frozen protocol abort clause fired."""


def http_get(url: str, *, timeout: int = 60, tries: int = 3) -> bytes:
    """GET with polite retries. HTTP 429 aborts the run (protocol clause)."""
    last: Exception | None = None
    for i in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                raise Abort(f"HTTP 429 at {url}")
            if e.code == 404:
                raise
            last = e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e
        time.sleep(5 * (i + 1))
    raise RuntimeError(f"GET failed after {tries}: {url}: {last!r}")


def load_index() -> dict:
    with gzip.open(INPUTS / "index.json.gz", "rt", encoding="utf-8") as f:
        return json.load(f)["wikis"]


def read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def read_rc(wiki: str) -> dict:
    """Recent-changes evidence for a wiki; stored gzipped after the run (evidence/rc/<wiki>.json.gz)."""
    gz = EVID / "rc" / f"{wiki}.json.gz"
    if gz.exists():
        with gzip.open(gz, "rt", encoding="utf-8") as f:
            return json.load(f)
    return read_json(EVID / "rc" / f"{wiki}.json")
