"""Historical collection script (network). It documents how the evidence was collected; the supported
operation for this bundle is the offline recompute in RESULT.md. Its download and time limits are not enforced
(see the correction in PROTOCOL.md section 7): run it only under disk, memory and wall-time limits applied
outside the script.

Compare legacy vs export records for one wiki and arm, classify each difference, live-confirm a capped sample.

usage: compare.py WIKI {current,history}
Difference types
  current: MISSING_EXPORT, MISSING_LEGACY (page_id only in one file), REV_DIFF (different latest rev),
           TEXT_DIFF (same rev, different text hash/presence), META_DIFF (same rev and text, other fields differ)
  history: MISSING_EXPORT, MISSING_LEGACY ((page_id, rev_id) only in one file), TEXT_DIFF, META_DIFF
Class: TIMING if a differing revision's timestamp >= W_START, or the page id or either title (or a move
target) appears in the recent-changes rows of W; else SNAPSHOT_LAG if the present side's revision timestamp
is later than the lacking side's wiki-wide maximum revision timestamp; otherwise UNEXPLAINED.
Live confirmation (UNEXPLAINED only, primary types, up to LIVE_CAP per wiki, random.Random(SEED)):
  EXPORT_WRONG / LEGACY_WRONG / UNCONFIRMED by the frozen rules in PROTOCOL.md section 5.
Writes evidence/compare/<arm>/<wiki>.json.
"""
from __future__ import annotations

import gzip
import json
import random
import sys
from collections import Counter

from common import BULK, EVID, SEED, W_END, W_START, read_json, read_rc, write_json
from rcfetch import api, api_url

LIVE_CAP = 200
ADJ_START = "2026-09-01T00:00:00Z"  # log-event adjudication window start (ends at W_END)
PRIMARY = ("MISSING_EXPORT", "MISSING_LEGACY", "REV_DIFF", "TEXT_DIFF")
META_FIELDS = ("ns", "title", "redirect", "ts", "user", "uid", "ip", "cdel", "comment_sha1", "cmdel", "model",
               "format", "bytes_attr", "sha1_attr", "tdel", "minor")


def b36_to_hex(s: str | None) -> str | None:
    if not s:
        return None
    return format(int(s, 36), "040x")


def load(arm: str, wiki: str, side: str) -> dict:
    out = {}
    for part in sorted((BULK / arm / wiki / f"{side}.parts").glob("*.jsonl.gz")):
        with gzip.open(part, "rt", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                key = r["pid"] if arm == "current" else (r["pid"], r["rid"])
                if key in out:  # duplicate key inside one file set is itself recorded
                    out.setdefault("__dups__", []).append(key)
                    continue
                out[key] = r
    return out


def integrity_one(c: Counter, r: dict) -> None:
    if True:
        if r["text_sha1"] is not None and r["sha1_attr"] and b36_to_hex(r["sha1_attr"]) != r["text_sha1"]:
            c["sha1_attr_mismatch"] += 1
        if r["text_len"] is not None and r["bytes_attr"] and int(r["bytes_attr"]) != r["text_len"]:
            c["bytes_attr_mismatch"] += 1
        if r["text_sha1"] is None and not r["tdel"]:
            c["no_text_not_deleted"] += 1
        if r["text_len"] == 0 and r["bytes_attr"] not in (None, "0"):
            c["empty_text_nonzero_bytes"] += 1


def integrity(recs: dict) -> Counter:
    c = Counter()
    for k, r in recs.items():
        if k != "__dups__":
            integrity_one(c, r)
    return c


COMPARED = ("rid", "text_sha1", "tdel") + META_FIELDS


def iter_side(arm: str, wiki: str, side: str):
    for part in sorted((BULK / arm / wiki / f"{side}.parts").glob("*.jsonl.gz")):
        with gzip.open(part, "rt", encoding="utf-8") as f:
            for line in f:
                yield json.loads(line)


def load_lean(arm: str, wiki: str) -> tuple[dict, dict, dict]:
    """Memory-lean equivalent of load()+full comparison for very large wikis (amendment 02).
    Pass 1 keeps a hash of the compared fields per key (first occurrence wins, as in load());
    pass 2 loads full records only for keys whose hashes differ or that exist on one side only.
    Records equal on every compared field never produce a difference in classify(), so the
    resulting difference list is identical to the full method."""
    import hashlib as _h
    stats = {}
    hashes = {}
    for side in ("legacy", "export"):
        h, c, dups, mx, n = {}, Counter(), 0, "", 0
        for r in iter_side(arm, wiki, side):
            key = r["pid"] if arm == "current" else (r["pid"], r["rid"])
            if key in h:
                dups += 1
                continue
            h[key] = _h.blake2b(json.dumps([r.get(f) for f in COMPARED], ensure_ascii=False).encode(), digest_size=8).digest()
            integrity_one(c, r)
            if r["ts"] and r["ts"] > mx:
                mx = r["ts"]
            n += 1
        hashes[side] = h
        stats[side] = {"integrity": dict(c), "dups": dups, "max_ts": mx, "n": n}
    hl, he = hashes["legacy"], hashes["export"]
    want = {k for k in hl if he.get(k) != hl[k]} | {k for k in he if k not in hl}
    del hashes, hl, he
    sub = {}
    for side in ("legacy", "export"):
        d = {}
        for r in iter_side(arm, wiki, side):
            key = r["pid"] if arm == "current" else (r["pid"], r["rid"])
            if key in want and key not in d:
                d[key] = r
        sub[side] = d
    return sub["legacy"], sub["export"], stats


def norm_text(r: dict):
    return (r["text_sha1"], r["tdel"])


FIELDS = ("rid", "ts", "title", "ns", "text_sha1", "text_len", "tdel", "sha1_attr", "redirect", "file")


def classify(arm: str, L: dict, E: dict, rc: dict, mx: dict | None = None) -> list[dict]:
    t_pid = {r["pageid"] for r in rc["rows"] if r.get("pageid")}
    t_title = {r["title"] for r in rc["rows"] if r.get("title")} | {r["target"] for r in rc["rows"] if r.get("target")}
    if mx is None:
        mx = {"legacy": max((r["ts"] for r in L.values() if r["ts"]), default=""),
              "export": max((r["ts"] for r in E.values() if r["ts"]), default="")}
    diffs = []
    for k in sorted(set(L) | set(E), key=lambda x: x if isinstance(x, tuple) else (x,)):
        a, b = L.get(k), E.get(k)
        lag = False
        if a and not b:
            typ, lag = "MISSING_EXPORT", (a["ts"] or "") > mx["export"]
        elif b and not a:
            typ, lag = "MISSING_LEGACY", (b["ts"] or "") > mx["legacy"]
        elif arm == "current" and a["rid"] != b["rid"]:
            typ = "REV_DIFF"
            newer, lacking = (a, "export") if (a["ts"] or "") > (b["ts"] or "") else (b, "legacy")
            lag = (newer["ts"] or "") > mx[lacking]
        elif norm_text(a) != norm_text(b):
            typ = "TEXT_DIFF"
        else:
            fields = [f for f in META_FIELDS if a.get(f) != b.get(f)]
            if not fields:
                continue
            typ = "META_DIFF"
        recs = [r for r in (a, b) if r]
        pid = recs[0]["pid"]
        timing = (any((r["ts"] or "") >= W_START for r in recs) or pid in t_pid
                  or any(r["title"] in t_title for r in recs))
        d = {"key": k, "type": typ, "class": "TIMING" if timing else ("SNAPSHOT_LAG" if lag else "UNEXPLAINED"),
             "legacy": None if not a else {f: a[f] for f in FIELDS},
             "export": None if not b else {f: b[f] for f in FIELDS}}
        if typ == "META_DIFF":
            d["fields"] = fields
        diffs.append(d)
    return diffs


def main_sha1(rev: dict) -> str | None:
    slot = (rev.get("slots") or {}).get("main") or {}
    if slot.get("sha1hidden") or rev.get("sha1hidden"):
        return None
    return slot.get("sha1")


def confirm(arm: str, wiki: str, checked: list[dict]) -> None:
    """Live confirmation (PROTOCOL section 5) plus log-event adjudication of every confirmed case."""
    if not checked:
        return
    base = api_url(wiki)
    rvprop = "ids|timestamp|sha1|size|slotsha1"
    pids = sorted({d["key"] if arm == "current" else d["key"][0] for d in checked})
    latest = {}
    for i in range(0, len(pids), 50):
        q = api(base, {"action": "query", "pageids": "|".join(map(str, pids[i:i + 50])), "prop": "revisions",
                       "rvprop": rvprop, "rvslots": "main"})
        for p in q["query"]["pages"]:
            latest[p["pageid"]] = None if p.get("missing") else (p["revisions"][0] if p.get("revisions") else None)
    rids = sorted({x["rid"] for d in checked for x in (d["legacy"], d["export"]) if x})
    revinfo = {}
    for i in range(0, len(rids), 50):
        q = api(base, {"action": "query", "revids": "|".join(map(str, rids[i:i + 50])), "prop": "revisions",
                       "rvprop": rvprop, "rvslots": "main"})
        for p in q["query"].get("pages", []):
            for r in p.get("revisions", []):
                revinfo[r["revid"]] = {"page": p["pageid"], **r}
        for bad in q["query"].get("badrevids", {}).values():
            revinfo[bad["revid"]] = {"bad": True}
    for d in checked:
        pid = d["key"] if arm == "current" else d["key"][0]
        lv = latest.get(pid)
        a, b = d["legacy"], d["export"]
        verdict = "UNCONFIRMED"
        if d["type"] == "TEXT_DIFF":
            ri = revinfo.get(a["rid"], {})
            live = None if not ri or ri.get("bad") else main_sha1(ri)
            if live:
                ok_l, ok_e = a["text_sha1"] == live, b["text_sha1"] == live
                verdict = ("EXPORT_WRONG" if ok_l and not ok_e else "LEGACY_WRONG" if ok_e and not ok_l else
                           "BOTH_WRONG" if not ok_l and not ok_e else "UNCONFIRMED")
        elif arm == "current":
            if d["type"] == "MISSING_EXPORT" and lv and lv["revid"] == a["rid"]:
                verdict = "EXPORT_WRONG"
            elif d["type"] == "MISSING_LEGACY" and lv and lv["revid"] == b["rid"]:
                verdict = "LEGACY_WRONG"
            elif d["type"] == "REV_DIFF" and lv and lv["timestamp"] < W_START:
                verdict = ("EXPORT_WRONG" if lv["revid"] == a["rid"] else
                           "LEGACY_WRONG" if lv["revid"] == b["rid"] else "UNCONFIRMED")
        else:
            ri = revinfo.get((a or b)["rid"], {})
            live = None if not ri or ri.get("bad") or ri.get("page") != pid else main_sha1(ri)
            if d["type"] == "MISSING_EXPORT" and live and live == a["text_sha1"]:
                verdict = "EXPORT_WRONG"
            elif d["type"] == "MISSING_LEGACY" and live and live == b["text_sha1"]:
                verdict = "LEGACY_WRONG"
        d["live"] = {"verdict": verdict, "latest": lv, "rev": revinfo.get((a or b)["rid"])}
    # adjudication: any delete/restore/move/import/merge/protect log event on either title in
    # [ADJ_START, W_END] turns a confirmation into METHOD_SUSPECT (not counted as a defect)
    for d in checked:
        if d["live"]["verdict"] not in ("EXPORT_WRONG", "LEGACY_WRONG"):
            continue
        events = []
        for t in sorted({x["title"] for x in (d["legacy"], d["export"]) if x}):
            q = api(base, {"action": "query", "list": "logevents", "letitle": t, "lestart": W_END, "leend": ADJ_START,
                           "ledir": "older", "lelimit": "50", "leprop": "type|timestamp|title"})
            events += q["query"]["logevents"]
        d["live"]["adj_events"] = events
        if events:
            d["live"]["confirmed_as"] = d["live"]["verdict"]
            d["live"]["verdict"] = "METHOD_SUSPECT"


LEAN_ABOVE = 3_000_000  # revisions per side (amendment 02)


def main(wiki: str, arm: str, lean: bool | None = None) -> int:
    rc = read_rc(wiki)
    if lean is None:
        summ = json.loads((BULK / arm / wiki / "extract-summary.json").read_text())
        lean = max(summ["legacy"]["revisions"], summ["export"]["revisions"]) > LEAN_ABOVE
    if lean:
        L, E, st = load_lean(arm, wiki)
        dups = {s_: st[s_]["dups"] for s_ in st}
        mx = {s_: st[s_]["max_ts"] for s_ in st}
        diffs = classify(arm, L, E, rc, mx)
    else:
        L = load(arm, wiki, "legacy")
        E = load(arm, wiki, "export")
        dups = {"legacy": len(L.pop("__dups__", [])), "export": len(E.pop("__dups__", []))}
        st = None
        diffs = classify(arm, L, E, rc)
    cand = [d for d in diffs if d["class"] == "UNEXPLAINED" and d["type"] in PRIMARY]
    rng = random.Random(SEED)
    checked = cand if len(cand) <= LIVE_CAP else rng.sample(cand, LIVE_CAP)
    confirm(arm, wiki, checked)
    live = Counter(d["live"]["verdict"] for d in checked)
    scale = (len(cand) / len(checked)) if checked else 0.0
    if st:
        n_l, n_e, ts_l, ts_e = st["legacy"]["n"], st["export"]["n"], st["legacy"]["max_ts"], st["export"]["max_ts"]
        integ = {"legacy": st["legacy"]["integrity"], "export": st["export"]["integrity"]}
    else:
        n_l, n_e = len(L), len(E)
        ts_l = max((r["ts"] for r in L.values() if r["ts"]), default=None)
        ts_e = max((r["ts"] for r in E.values() if r["ts"]), default=None)
        integ = {"legacy": dict(integrity(L)), "export": dict(integrity(E))}
    out = {
        "wiki": wiki, "arm": arm, "n_legacy": n_l, "n_export": n_e, "dup_keys": dups, "lean": bool(st),
        "max_ts": {"legacy": ts_l, "export": ts_e},
        "rc_covers_window": rc["covers_window"], "rc_rows": rc["count"],
        "integrity": integ,
        "counts": {f"{d}|{c}": n for (d, c), n in sorted(Counter((x["type"], x["class"]) for x in diffs).items())},
        "unexplained_primary": len(cand), "live_checked": len(checked), "live": dict(live),
        "est_export_wrong": round(live.get("EXPORT_WRONG", 0) * scale),
        "est_legacy_wrong": round(live.get("LEGACY_WRONG", 0) * scale),
        "export_wrong_by_ns_type": dict(Counter(f"{(d['legacy'] or d['export'])['ns']}|{d['type']}" for d in checked
                                                if d["live"]["verdict"] == "EXPORT_WRONG")),
        "checked": checked, "n_diffs": len(diffs),
    }
    write_json(EVID / "compare" / arm / f"{wiki}.json", out)
    with gzip.open(EVID / "compare" / arm / f"{wiki}.diffs.jsonl.gz", "wt", encoding="utf-8") as g:
        for d in diffs:
            g.write(json.dumps(d, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps({k: out[k] for k in ("wiki", "arm", "n_legacy", "n_export", "counts", "unexplained_primary", "live", "max_ts")}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
