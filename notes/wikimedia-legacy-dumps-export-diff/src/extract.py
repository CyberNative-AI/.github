"""Stream-parse dump files into per-revision records (no text kept, only hashes and lengths).

usage: extract.py WIKI {current,history} [--procs N]
Writes BULK/<arm>/<wiki>/{legacy,export}.parts/<file>.jsonl.gz, one JSON per revision:
pid, ns, title, redirect, rid, parent, ts, user, uid, ip, cdel (contributor deleted), comment_sha1,
cmdel, model, format, bytes_attr, sha1_attr, tdel (text deleted attr), text_sha1 (hex, None if
no text element content), text_len (UTF-8 bytes), file.


On a full rerun the records written under DUMPS_WORK contain contributor user names, user IDs and IP
addresses (user, uid, ip). The published comparison evidence does not; redact these records before sharing them."""
from __future__ import annotations

import bz2
import gzip
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from multiprocessing import Pool
from pathlib import Path

from common import BULK

NS = "{http://www.mediawiki.org/xml/export-0.11/}"


def _t(el, tag):
    c = el.find(NS + tag)
    return None if c is None else (c.text or "")


def parse_file(args: tuple[str, str]) -> int:
    """Parse one bz2 dump file; write its records to a gz part file; return the revision count."""
    path, part = args
    n = 0
    page = {}
    root = None
    with bz2.open(path, "rb") as f, gzip.open(part, "wt", encoding="utf-8") as g:
        for ev, el in ET.iterparse(f, events=("start", "end")):
            tag = el.tag
            if ev == "start":
                if root is None:
                    root = el
                if tag == NS + "page":
                    page = {}
                continue
            if tag == NS + "revision":
                contrib = el.find(NS + "contributor")
                text = el.find(NS + "text")
                comment = el.find(NS + "comment")
                tx = None if text is None else text.text
                rec = {
                    "pid": int(page["pid"]), "ns": int(page["ns"]), "title": page["title"],
                    "redirect": page.get("redirect"),
                    "rid": int(_t(el, "id")), "parent": _t(el, "parentid"), "ts": _t(el, "timestamp"),
                    "user": None if contrib is None else _t(contrib, "username"),
                    "uid": None if contrib is None else _t(contrib, "id"),
                    "ip": None if contrib is None else _t(contrib, "ip"),
                    "cdel": None if contrib is None else contrib.get("deleted"),
                    "minor": el.find(NS + "minor") is not None,
                    "comment_sha1": None if comment is None or comment.text is None
                    else hashlib.sha1(comment.text.encode("utf-8")).hexdigest(),
                    "cmdel": None if comment is None else comment.get("deleted"),
                    "model": _t(el, "model"), "format": _t(el, "format"),
                    "bytes_attr": None if text is None else text.get("bytes"),
                    "sha1_attr": _t(el, "sha1"),
                    "tdel": None if text is None else text.get("deleted"),
                    "text_sha1": None if tx is None else hashlib.sha1(tx.encode("utf-8")).hexdigest(),
                    "text_len": None if tx is None else len(tx.encode("utf-8")),
                    "file": Path(path).name,
                }
                g.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
                n += 1
                el.clear()
            elif tag == NS + "title":
                page["title"] = el.text
            elif tag == NS + "ns":
                page["ns"] = el.text
            elif tag == NS + "id" and "pid" not in page and "title" in page:
                page["pid"] = el.text
            elif tag == NS + "redirect":
                page["redirect"] = el.get("title")
            elif tag in (NS + "page", NS + "siteinfo"):
                root.clear()  # drop finished pages from the tree (bounded memory)
    return n


def main(wiki: str, arm: str, procs: int = 4) -> int:
    root = BULK / arm / wiki
    summary = {}
    for side in ("legacy", "export"):
        files = sorted(str(p) for p in (root / side).glob("*.bz2"))
        (root / f"{side}.parts").mkdir(exist_ok=True)
        jobs = [(f, str(root / f"{side}.parts" / (Path(f).name + ".jsonl.gz"))) for f in files]
        with Pool(min(procs, max(1, len(files)))) as pool:
            counts = pool.map(parse_file, jobs)
        summary[side] = {"files": len(files), "revisions": sum(counts)}
    (root / "extract-summary.json").write_text(json.dumps(summary, sort_keys=True))
    print(json.dumps({"wiki": wiki, "arm": arm, **summary}))
    return 0


if __name__ == "__main__":
    procs = int(sys.argv[sys.argv.index("--procs") + 1]) if "--procs" in sys.argv else 4
    sys.exit(main(sys.argv[1], sys.argv[2], procs))
