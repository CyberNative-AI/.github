"""Historical collection script (network). It documents how the evidence was collected; the supported
operation for this bundle is the offline recompute in RESULT.md. Its download and time limits are not enforced
(see the correction in PROTOCOL.md section 7): run it only under disk, memory and wall-time limits applied
outside the script.

Amendment 01 (post hoc, descriptive; does not change the verdict): root-cause signatures of the
live-confirmed EXPORT_WRONG cases.

For the first CAP (by key) EXPORT_WRONG cases per wiki and type in evidence/compare/current/*.json, query the public API for
  - the comment of the revision in question (is it a page-move null revision?),
  - all log events on the title (any time): move, delete, restore, import, merge, protect,
  - whether the page is now a redirect.
Writes evidence/signatures.jsonl (resumable) and prints a per-type summary.
Prior-art hypotheses: TEXT_DIFF with empty export text = T417596 regression ("moved articles don't have
any page text", reopened 2026-09-14); MISSING_EXPORT = a separate, unreported mechanism unless moves explain it.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta

from common import EVID, read_json
from rcfetch import api, api_url

OUT = EVID / "signatures.jsonl"
MOVE_WORDS = ("moved page", "moved", "move")
CAP = 15


def main() -> int:
    done = set()
    if OUT.exists():
        done = {(json.loads(l)["arm"], json.loads(l)["wiki"], str(json.loads(l)["key"])) for l in OUT.read_text().splitlines() if l.strip()}
    for arm in ("current",):  # history arm repeats the same pages; capped at CAP cases per (wiki, type)
        for p in sorted((EVID / "compare" / arm).glob("*.json")):
            c = read_json(p)
            cases = []
            for typ in ("MISSING_EXPORT", "TEXT_DIFF", "REV_DIFF"):
                cases += sorted((d for d in c.get("checked", []) if d["live"]["verdict"] == "EXPORT_WRONG"
                                 and d["type"] == typ), key=lambda d: str(d["key"]))[:CAP]
            if not cases:
                continue
            base = api_url(c["wiki"])
            for d in cases:
                if (arm, c["wiki"], str(d["key"])) in done:
                    continue
                rec = d["legacy"] or d["export"]
                q = api(base, {"action": "query", "revids": str(rec["rid"]), "prop": "revisions|info",
                               "rvprop": "ids|timestamp|comment|size"})
                pages = q["query"].get("pages", [])
                rev = (pages[0].get("revisions") or [{}])[0] if pages else {}
                lg = api(base, {"action": "query", "list": "logevents", "letitle": rec["title"], "lelimit": "50",
                                "leprop": "type|timestamp|details"})
                ev = [{"type": e["type"], "action": e.get("action"), "ts": e["timestamp"]} for e in lg["query"]["logevents"]]
                # a page move writes a null revision on the target title at the move's timestamp:
                # look for move log entries within +-2 s of this revision whose target is this title
                t0 = datetime.strptime(rec["ts"], "%Y-%m-%dT%H:%M:%SZ")
                mv = api(base, {"action": "query", "list": "logevents", "letype": "move", "lelimit": "500",
                                "leprop": "title|timestamp|details", "ledir": "older",
                                "lestart": (t0 + timedelta(seconds=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "leend": (t0 - timedelta(seconds=2)).strftime("%Y-%m-%dT%H:%M:%SZ")})
                moved_into = [e["timestamp"] for e in mv["query"]["logevents"]
                              if (e.get("params") or {}).get("target_title") == rec["title"]][:3]
                out = {"model_legacy_bytes0": (d["legacy"] or {}).get("text_len") and (d["export"] or {}).get("text_len") is None,
                       "arm": arm, "wiki": c["wiki"], "key": d["key"], "type": d["type"], "ns": rec["ns"],
                       "rid": rec["rid"], "ts": rec["ts"], "text_len_legacy": (d["legacy"] or {}).get("text_len"),
                       "comment": rev.get("comment"), "is_redirect": bool(pages and pages[0].get("redirect")),
                       "log": ev, "moved_into_at": moved_into}
                with OUT.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(out, sort_keys=True, ensure_ascii=False) + "\n")
    rows = [json.loads(l) for l in OUT.read_text().splitlines() if l.strip()]
    summ = Counter()
    for r in rows:
        movey = bool(r["comment"] and any(w in r["comment"].lower() for w in MOVE_WORDS)) or bool(r["moved_into_at"]) \
            or any(e["type"] == "move" for e in r["log"])
        summ[(r["arm"], r["type"], "move-related" if movey else "no-move-signal", "redirect" if r["is_redirect"] else "non-redirect")] += 1
    for k, v in sorted(summ.items()):
        print(k, v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
