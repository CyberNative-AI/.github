"""Build the frame and the seeded size-stratified sample (no dump content is read here).

Frame: wikis whose legacy 20261001 metacurrentdump is 'done' (inputs/index.json.gz).
Coverage arm C: frame wikis without a mediawiki_content_current directory, by sitematrix status.
Sample: wikis present in both listings, legacy current size <= 300 MB, excluding the pilot wiki,
8 per size bin, random.Random(SEED). Targeted arm T: enwiktionary (T417596 site) plus one wiki drawn with
random.Random(SEED + 1) from the [300 MB, 2.5 GB) current-size pool (scale check).
"""
from __future__ import annotations

import gzip
import json
import random
import re

from common import INPUTS, LAB, LEGACY_DATE, SEED, load_index, write_json

BINS = [(0, 1_150_000), (1_150_000, 5_000_000), (5_000_000, 25_000_000), (25_000_000, 300_000_000)]
PER_BIN = 8
EXCLUDE = {"punjabiwikimedia"}  # design-time format pilot
TARGETED = ["enwiktionary"]


def sitematrix_status() -> dict:
    with gzip.open(INPUTS / "sitematrix.json.gz", "rt", encoding="utf-8") as f:
        sm = json.load(f)["sitematrix"]
    out = {}
    for k, v in sm.items():
        if k == "count":
            continue
        for s in (v if k == "specials" else v["site"]):
            out[s["dbname"]] = {"closed": "closed" in s, "private": "private" in s, "fishbowl": "fishbowl" in s}
    return out


def main() -> None:
    idx = load_index()
    exp = set((INPUTS / "export_dirs.txt").read_text().split())
    hexp = set((INPUTS / "export_hist_dirs.txt").read_text().split())
    sm = sitematrix_status()
    frame = {}
    for w, v in sorted(idx.items()):
        jobs = v.get("jobs", {})
        mc = jobs.get("metacurrentdump", {})
        files = mc.get("files", {})
        if mc.get("status") != "done" or not files:
            continue
        if not all(re.search(rf"-{LEGACY_DATE}-", f) for f in files):
            continue
        mh = jobs.get("metahistorybz2dump", {})
        frame[w] = {
            "cur_files": {f: {"size": x["size"], "sha1": x.get("sha1"), "url": x["url"]} for f, x in sorted(files.items())},
            "cur_size": sum(x["size"] for x in files.values()),
            "hist_status": mh.get("status"),
            "hist_files": {f: {"size": x["size"], "sha1": x.get("sha1"), "url": x["url"]} for f, x in sorted(mh.get("files", {}).items())},
            "hist_size": sum(x["size"] for x in mh.get("files", {}).values()),
            "in_export_current": w in exp,
            "in_export_history": w in hexp,
            "sitematrix": sm.get(w),
            "stubs_updated": jobs.get("xmlstubsdump", {}).get("updated"),
            "metacurrent_updated": mc.get("updated"),
        }
    cov = {"frame": len(frame), "missing_current_export": sorted(w for w, r in frame.items() if not r["in_export_current"])}
    cov["missing_by_status"] = {}
    for w in cov["missing_current_export"]:
        s = frame[w]["sitematrix"] or {}
        key = "closed" if s.get("closed") else ("open" if s else "not_in_sitematrix")
        cov["missing_by_status"][key] = cov["missing_by_status"].get(key, 0) + 1
    rng = random.Random(SEED)
    sample = []
    for lo, hi in BINS:
        pool = sorted(w for w, r in frame.items()
                      if r["in_export_current"] and w not in EXCLUDE and w not in TARGETED and lo <= r["cur_size"] < hi)
        pick = sorted(rng.sample(pool, PER_BIN))
        sample += [{"wiki": w, "bin": f"{lo}-{hi}", "pool": len(pool)} for w in pick]
    large_pool = sorted(w for w, r in frame.items() if r["in_export_current"] and w not in TARGETED
                        and 300_000_000 <= r["cur_size"] < 2_500_000_000)
    large = sorted(random.Random(SEED + 1).sample(large_pool, 1))
    hist = [s["wiki"] for s in sample
            if frame[s["wiki"]]["hist_status"] == "done" and 0 < frame[s["wiki"]]["hist_size"] <= 300_000_000
            and frame[s["wiki"]]["in_export_history"]]
    write_json(LAB / "evidence" / "frame.json", frame)
    write_json(LAB / "evidence" / "sample.json", {"seed": SEED, "per_bin": PER_BIN, "bins": BINS, "sample": sample,
                                                  "targeted": TARGETED + large, "large_pool": len(large_pool),
                                                  "history_arm": hist, "coverage": cov})
    print(json.dumps({"frame": len(frame), "sample": [s["wiki"] for s in sample], "history_arm": hist,
                      "coverage_missing": len(cov["missing_current_export"]), "by_status": cov["missing_by_status"]}, indent=1))


if __name__ == "__main__":
    main()
