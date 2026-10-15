"""Regenerate evidence/tallies.json from stored evidence only (offline, no network, no dump files).

Inputs: evidence/summary.json (written by summarise.py), evidence/frame.json, evidence/coverage-editions.jsonl,
evidence/compare/current/*.json, evidence/compare/current/*.diffs.jsonl.gz and evidence/signatures.jsonl.
Signature labels are post hoc (Amendment 01) and do not feed the verdict.
All current_* counts, title_style_* and signature_check cover the random sample only. The two targeted large wikis
are reported separately under "targeted" (they were not part of the sample and do not feed the verdict).

  S1_proofread_len0  confirmed TEXT_DIFF in the ProofreadPage namespace (104) with no export text
  S2_wikitext_empty  confirmed TEXT_DIFF elsewhere with no export text
  MISSING_EXPORT_*   confirmed missing page, split by the legacy redirect flag
"""
from __future__ import annotations

import gzip
import json
from collections import Counter

from common import EVID, read_json, write_json

PROOFREAD_PAGE_NS = 104
# A move writes a null revision on its target. Signals: a move log entry targeting the title within +-2 s
# (moved_into_at), or the move edit summary. English summaries say "moved"; ruewiki's says "переменовав сторінку".
MOVE_WORDS = ("moved", "move", "переменовав сторінку")


def move_comment(r: dict) -> bool:
    if "comment_move_summary" in r:  # public copy: summary text removed, this flag kept
        return bool(r["comment_move_summary"])
    return bool(r["comment"] and any(w in r["comment"].lower() for w in MOVE_WORDS))


def label(d: dict) -> str:
    v = d["live"]["verdict"]
    if v != "EXPORT_WRONG":
        return f"other|{v}"
    if d["type"] == "MISSING_EXPORT":
        return "MISSING_EXPORT_redirect" if d["legacy"]["redirect"] is not None else "MISSING_EXPORT_nonredirect"
    if d["type"] == "TEXT_DIFF" and (d["export"] or {}).get("text_len") is None:
        return "S1_proofread_len0" if d["legacy"]["ns"] == PROOFREAD_PAGE_NS else "S2_wikitext_empty"
    return d["type"]


def main() -> int:
    summ = read_json(EVID / "summary.json")
    s = read_json(EVID / "sample.json")
    frame = read_json(EVID / "frame.json")
    eds = [json.loads(l) for l in (EVID / "coverage-editions.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    closed = {w for w, v in frame.items() if v["sitematrix"]["closed"]}
    both = {e["wiki"] for e in eds if e["mediawiki_content_current"] == 200 and e["mediawiki_content_history"] == 200}
    with_dir = {e["wiki"] for e in eds}

    sample = [x["wiki"] for x in s["sample"]]
    by_sig, by_sig_wiki, est, title_style = Counter(), Counter(), {}, Counter()
    targeted = {}
    for p in sorted((EVID / "compare" / "current").glob("*.json")):
        c = read_json(p)
        if c["wiki"] in s["targeted"]:
            t_sig, t_title = Counter(), 0
            for d in c.get("checked", []):
                t_sig[label(d)] += 1
            with gzip.open(p.with_suffix(".diffs.jsonl.gz"), "rt", encoding="utf-8") as f:
                for line in f:
                    d = json.loads(line)
                    if d["type"] == "META_DIFF" and "title" in d["fields"]:
                        t_title += 1
            targeted[c["wiki"]] = {"n_legacy": c["n_legacy"], "n_export": c["n_export"], "counts": c["counts"],
                                   "live_checked": c["live_checked"], "confirmed_by_signature": dict(t_sig),
                                   "est_export_wrong": c["est_export_wrong"], "est_legacy_wrong": c["est_legacy_wrong"],
                                   "title_style_meta_diffs": t_title}
            continue
        if c["wiki"] not in sample:
            continue
        for d in c.get("checked", []):
            lab = label(d)
            by_sig[lab] += 1
            if not lab.startswith("other|"):
                by_sig_wiki[f"{lab}|{c['wiki']}"] += 1
        if c["est_export_wrong"]:
            est[c["wiki"]] = c["est_export_wrong"]
        with gzip.open(p.with_suffix(".diffs.jsonl.gz"), "rt", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                # any class, as first reported; 5 of these are TIMING-class (bowiki 1, ruewiki 4)
                if d["type"] == "META_DIFF" and "title" in d["fields"]:
                    title_style[c["wiki"]] += 1

    sig = [json.loads(l) for l in (EVID / "signatures.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    sig = [r for r in sig if r["arm"] == "current" and r["wiki"] in sample]
    s1 = [r for r in sig if r["type"] == "TEXT_DIFF" and r["ns"] == PROOFREAD_PAGE_NS]
    s2 = [r for r in sig if r["type"] == "TEXT_DIFF" and r["ns"] != PROOFREAD_PAGE_NS]
    miss = [r for r in sig if r["type"] == "MISSING_EXPORT"]
    moved = lambda r: bool(r["moved_into_at"]) or move_comment(r) or any(e["type"] == "move" for e in r["log"])

    usable = lambda arm, w: f"{arm}:{w}" in summ["rows"] and not any(u.startswith(f"{arm}:{w}:") for u in summ["unusable"])
    out = {
        "coverage": {"frame": len(frame), "open_wikis": len(frame) - len(closed), "closed_wikis": len(closed),
                     "open_with_both_editions": len(both - closed), "closed_no_dir": len(closed - with_dir),
                     "closed_empty_dir": len((closed & with_dir) - both)},
        "current_confirmed_by_signature": dict(by_sig),
        "current_confirmed_by_signature_wiki": dict(by_sig_wiki),
        "current_est_export_wrong_by_wiki": est,
        "current_est_total": sum(est.values()),
        "history_drawn": len(s["history_arm"]),
        "history_usable": sum(usable("history", w) for w in s["history_arm"]),
        "history_with_export_defect": len(summ["history_wikis_with_confirmed_export_defect"]),
        "sample_drawn": len(sample),
        "sample_usable": sum(usable("current", w) for w in sample),
        "sample_with_export_defect": len(summ["sample_wikis_with_confirmed_export_defect"]),
        "signature_check": {"S1_checked": len(s1), "S1_move_signal": sum(map(moved, s1)),
                            "S2_checked": len(s2), "S2_move_null_revision": sum(map(moved, s2)),
                            "missing_checked": len(miss), "missing_redirect_now": sum(r["is_redirect"] for r in miss)},
        "targeted": targeted,
        "title_style_meta_diffs_by_wiki": dict(title_style),
        "unusable": summ["unusable"],
        "verdict": summ["verdict"],
    }
    write_json(EVID / "tallies.json", out)
    print(json.dumps({k: out[k] for k in ("verdict", "sample_with_export_defect", "sample_usable",
                                          "history_with_export_defect", "history_usable", "current_est_total")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
