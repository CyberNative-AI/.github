"""Frozen analysis: does today's NWS CAP stream, with the VTEC parameter removed,
still let a consumer (P1) group alerts into the same events and (P2) detect when an event ends?

Gold labels come from the VTEC parameter; CAP-only reconstructions never read it.
Usage: python3 src/analyze.py RAW_DIR OUT_DIR
"""
from __future__ import annotations

import collections
import datetime as dt
import glob
import hashlib
import json
import re
import sys
from pathlib import Path

VTEC_RE = re.compile(
    r"^/([OTEX])\.([A-Z]{3})\.([A-Z]{4})\.([A-Z]{2})\.([A-Z])\.(\d{4})\."
    r"(\d{6}T\d{4}Z)-(\d{6}T\d{4}Z)/$"
)
END_ACTIONS = {"CAN", "EXP", "UPG"}
END_TEXT_RE = re.compile(
    r"\b(HAS|HAVE) (BEEN )?(EXPIRED|CANCELL?ED|ALLOWED TO EXPIRE)\b|\bWILL (BE ALLOWED TO )?EXPIRE\b|\b(IS|ARE) CANCELL?ED\b"
)
TOL_MIN = 10  # primary tolerance for the time-based end rule (sensitivity: 0 and 30)


def parse_time(s: str | None) -> dt.datetime | None:
    if not s:
        return None
    return dt.datetime.fromisoformat(s)


def parse_vtec(s: str) -> dict | None:
    m = VTEC_RE.match(s.strip())
    if not m:
        return None
    k, act, off, ph, sig, etn, beg, end = m.groups()
    return {"k": k, "action": act, "office": off, "phen": ph, "sig": sig, "etn": int(etn),
            "begin": beg, "end": end, "key": f"{off}.{ph}.{sig}.{int(etn)}"}


def load(raw_dir: Path) -> tuple[list[dict], dict]:
    seen: dict[str, dict] = {}
    stats = collections.Counter()
    for p in sorted(glob.glob(str(raw_dir / "page-*.json"))):
        for f in json.loads(Path(p).read_text(encoding="utf-8"))["features"]:
            pr = f["properties"]
            stats["rows"] += 1
            if pr["id"] in seen:
                stats["duplicate_rows"] += 1
                continue
            seen[pr["id"]] = pr
    alerts = [pr for pr in seen.values() if pr.get("status") == "Actual"]
    stats["unique"] = len(seen)
    stats["actual"] = len(alerts)
    for p in sorted(glob.glob(str(raw_dir / "extra" / "*.json"))):
        try:
            pr = json.loads(Path(p).read_text(encoding="utf-8"))["properties"]
        except (ValueError, KeyError):
            stats["extra_unreadable"] += 1
            continue
        if pr["id"] in seen:
            continue
        seen[pr["id"]] = pr
        stats["extra_loaded"] += 1
        if pr.get("status") == "Actual":
            pr["_extra"] = True
            alerts.append(pr)
    return alerts, dict(stats)


def ref_ids(a: dict, expired: bool = True) -> list[str]:
    ids = [r.get("identifier") for r in a.get("references") or [] if r.get("identifier")]
    if expired:
        for s in (a.get("parameters") or {}).get("expiredReferences") or []:
            ids += [t.split(",")[1] for t in s.split() if t.count(",") >= 2]
    return ids


class DSU:
    def __init__(self) -> None:
        self.p: dict[str, str] = {}

    def find(self, x: str) -> str:
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


def components(alerts: list[dict], strict: bool, expired: bool = True, edges: bool = True) -> dict[str, str]:
    """R0 (edges=False): no edges (floor). R1 (strict=False): connected components over CAP `references` plus
    `parameters.expiredReferences` (unknown referenced ids are nodes). R2 (strict=True): only edges whose two ends are
    both known and share `event` and `senderName`. expired=False drops expiredReferences edges."""
    by_id = {a["id"]: a for a in alerts}
    d = DSU()
    for a in alerts:
        d.find(a["id"])
        if not edges:
            continue
        for rid in ref_ids(a, expired):
            if strict:
                b = by_id.get(rid)
                if b is None or b["event"] != a["event"] or b.get("senderName") != a.get("senderName"):
                    continue
            d.union(a["id"], rid)
    return {a["id"]: d.find(a["id"]) for a in alerts}


def ends_soon(a: dict, tol_min: int) -> bool:
    sent = parse_time(a["sent"])
    t = parse_time(a.get("ends")) or parse_time(a.get("expires"))
    return t is not None and t <= sent + dt.timedelta(minutes=tol_min)


def end_text(a: dict) -> bool:
    p = a.get("parameters") or {}
    t = " ".join([a.get("headline") or "", " ".join(p.get("NWSheadline") or []), a.get("description") or ""])
    return bool(END_TEXT_RE.search(t.upper()))


def end_pred(a: dict, tol_min: int, kind: str = "E2") -> bool:
    """E2 (primary): messageType Cancel OR time rule OR text rule. E1: messageType only. ET: time only. EX: text only."""
    if kind == "E1":
        return a["messageType"] == "Cancel"
    if kind == "ET":
        return ends_soon(a, tol_min)
    if kind == "EX":
        return end_text(a)
    return a["messageType"] == "Cancel" or ends_soon(a, tol_min) or end_text(a)


def analyze(alerts: list[dict], load_stats: dict) -> dict:
    vt_alerts = []  # (alert, parsed vtec)
    vstats = collections.Counter()
    snap = [a for a in alerts if not a.get("_extra")]
    snap_end = max(parse_time(a["sent"]) for a in snap)
    for a in alerts:
        vs = (a.get("parameters") or {}).get("VTEC") or []
        vstats[f"vtec_per_alert_{min(len(vs), 2)}"] += 1
        for s in vs:
            v = parse_vtec(s)
            if v is None:
                vstats["vtec_parse_fail"] += 1
                continue
            vstats["vtec_strings"] += 1
            if v["k"] != "O":
                vstats["vtec_non_operational"] += 1
                continue
            vt_alerts.append((a, v))
    multi = [a["id"] for a in alerts if len((a.get("parameters") or {}).get("VTEC") or []) > 1]

    # event membership from VTEC (gold)
    ev_alerts: dict[str, set[str]] = collections.defaultdict(set)
    ev_actions: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    alert_keys: dict[str, set[str]] = collections.defaultdict(set)
    for a, v in vt_alerts:
        ev_alerts[v["key"]].add(a["id"])
        ev_actions[v["key"]][v["action"]] += 1
        alert_keys[a["id"]].add(v["key"])
    # gold events counted only from listing-snapshot alerts; fetched extras are graph nodes and purity labels
    snap_ids = {a["id"] for a in snap}
    new_time: dict[str, dt.datetime] = {}
    for a, v in vt_alerts:
        if v["action"] == "NEW" and a["id"] in snap_ids:
            t = parse_time(a["sent"])
            new_time[v["key"]] = min(t, new_time.get(v["key"], t))
    all_new = sorted(new_time)
    eval_sets = {
        "primary_ge2_alerts": [k for k in all_new if len(ev_alerts[k]) >= 2],
        "all_new_events": all_new,
        "ge2_and_new_ge48h_before_end": [k for k in all_new if len(ev_alerts[k]) >= 2
                                         and new_time[k] <= snap_end - dt.timedelta(hours=48)],
    }
    known0 = {a["id"] for a in alerts}
    by_id0 = {a["id"]: a for a in alerts}
    gap = {k for k in all_new if any(r not in known0 for aid in ev_alerts[k] for r in ref_ids(by_id0[aid]))}
    eval_sets["primary_excluding_gap_touched"] = [k for k in eval_sets["primary_ge2_alerts"] if k not in gap]
    eval_events = eval_sets["primary_ge2_alerts"]

    by_id = {a["id"]: a for a in alerts}
    known = {a["id"] for a in alerts}
    unresolved = {rid for a in alerts for rid in ref_ids(a) if rid not in known}
    out: dict = {"load": load_stats, "vtec": dict(vstats), "multi_vtec_alerts": len(multi),
                 "events_total": len(ev_alerts), "events_evaluated": len(eval_events),
                 "eval_set_sizes": {k: len(v) for k, v in eval_sets.items()},
                 "unresolved_referenced_ids": len(unresolved), "snapshot_last_sent": snap_end.isoformat()}
    rules = (("R0_no_edges", dict(strict=False, edges=False)),
             ("R1_references", dict(strict=False)),
             ("R2_references_same_event_sender", dict(strict=True)),
             ("R2a_references_only_same_event_sender", dict(strict=True, expired=False)))
    for name, kw in rules:
        comp = components(alerts, **kw)
        members: dict[str, set[str]] = collections.defaultdict(set)
        for aid, c in comp.items():
            members[c].add(aid)
        outcome = collections.Counter()
        examples: dict[str, list[str]] = collections.defaultdict(list)
        per_phensig: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
        for k in eval_events:
            comps = {comp[aid] for aid in ev_alerts[k]}
            split = len(comps) > 1
            other_keys = set()
            for c in comps:
                for aid in members[c]:
                    other_keys |= alert_keys.get(aid, set())
            other_keys.discard(k)
            merged = bool(other_keys)
            o = "exact" if not split and not merged else ("split+merged" if split and merged else ("split" if split else "merged"))
            outcome[o] += 1
            ps = ".".join(k.split(".")[1:3])
            per_phensig[ps][o] += 1
            if o != "exact" and len(examples[o]) < 15:
                examples[o].append(k)
        n = len(eval_events)
        sens = {}
        for sname, keys in eval_sets.items():
            ex = sum(1 for k in keys if len({comp[aid] for aid in ev_alerts[k]}) == 1 and not (
                {kk for c in {comp[aid] for aid in ev_alerts[k]} for aid in members[c] for kk in alert_keys.get(aid, set())} - {k}))
            sens[sname] = {"n": len(keys), "exact": ex, "share": ex / len(keys) if keys else None}
        out[name] = {"n": n, "outcomes": dict(outcome), "exact_share": outcome["exact"] / n if n else None,
                     "eval_set_sensitivity": sens,
                     "by_phen_sig": {p: dict(c) for p, c in sorted(per_phensig.items())},
                     "examples": dict(examples)}

    # P2: end detection per VTEC-bearing alert (operational, all collected Actual)
    p2 = {}
    p2_alerts = [(a, v) for a, v in vt_alerts if a["id"] in snap_ids]
    for kind, tol in (("E2", 0), ("E2", TOL_MIN), ("E2", 30), ("E1", 0), ("ET", TOL_MIN), ("EX", 0)):
        tab = collections.Counter()
        for a, v in p2_alerts:
            is_end = v["action"] in END_ACTIONS
            tab[(is_end, end_pred(a, tol, kind))] += 1
        ends = tab[(True, True)] + tab[(True, False)]
        non = tab[(False, True)] + tab[(False, False)]
        p2[f"{kind}_tol{tol}"] = {"end_alerts": ends, "end_detected": tab[(True, True)],
                           "recall": tab[(True, True)] / ends if ends else None,
                           "non_end_alerts": non, "false_end": tab[(False, True)],
                           "false_end_rate": tab[(False, True)] / non if non else None}
    out["P2_end_detection"] = p2
    xt = collections.Counter((v["action"], a["messageType"]) for a, v in p2_alerts)
    out["action_by_messageType"] = {f"{k[0]}|{k[1]}": n for k, n in sorted(xt.items())}

    # S3 descriptive: is the VTEC event number recoverable from non-VTEC text?
    s3 = collections.Counter()
    for a, v in p2_alerts:
        p = a.get("parameters") or {}
        text = " ".join([a.get("headline") or "", a.get("description") or "", " ".join(p.get("NWSheadline") or [])])
        nums = {int(x) for x in re.findall(r"\bWATCH\s+(?:NUMBER\s+)?(\d{1,4})\b", text.upper())}
        grp = "watch_TO_SV_A" if v["sig"] == "A" and v["phen"] in ("TO", "SV") else "other"
        s3[(grp, v["etn"] in nums)] += 1
    out["S3_etn_in_text"] = {f"{g}|{f}": n for (g, f), n in sorted(s3.items())}
    return out


def decide(r: dict) -> str:
    p1 = r["R2_references_same_event_sender"]["exact_share"]
    p2 = r["P2_end_detection"][f"E2_tol{TOL_MIN}"]
    invalid = []
    if r["load"]["actual"] < 5000:
        invalid.append("fewer than 5000 Actual alerts")
    if r["events_evaluated"] < 500:
        invalid.append("fewer than 500 evaluated events")
    if r["vtec"].get("vtec_strings", 0) and r["vtec"].get("vtec_parse_fail", 0) / (r["vtec"]["vtec_strings"] + r["vtec"].get("vtec_parse_fail", 0)) > 0.01:
        invalid.append("VTEC parse failures > 1%")
    if not p2["end_alerts"] or p2["end_alerts"] < 100:
        invalid.append("fewer than 100 ending alerts")
    if invalid:
        return "INVALID: " + "; ".join(invalid)
    if p1 < 0.95 or p2["recall"] < 0.95 or p2["false_end_rate"] > 0.05:
        return "CONTINUE"
    if p1 >= 0.99 and p2["recall"] >= 0.99 and p2["false_end_rate"] <= 0.01:
        return "STOP"
    return "CHANGE"


def main() -> None:
    raw, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    alerts, stats = load(raw)
    r = analyze(alerts, stats)
    r["decision"] = decide(r)
    r["inputs_sha256"] = {Path(p).name: hashlib.sha256(Path(p).read_bytes()).hexdigest()
                          for p in sorted(glob.glob(str(raw / "page-*.json")))}
    (out / "results.json").write_text(json.dumps(r, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: r[k] for k in ("decision", "events_evaluated")}, indent=1))
    print("P1 R2", r["R2_references_same_event_sender"]["outcomes"], "R1", r["R1_references"]["outcomes"])
    print("P2", json.dumps(r["P2_end_detection"]))


if __name__ == "__main__":
    main()
