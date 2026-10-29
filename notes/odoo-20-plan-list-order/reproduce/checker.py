#!/usr/bin/env python3
"""Independent feasibility checker and scorer. Stdlib only; shares no code with the arms.

  python3 checker.py --data DIR --schedule schedule.csv [--base-schedule base.csv] [--json out.json]

DIR is the ERP export the arm was given (work_centers, calendars, time_off, orders, work_orders,
export_info). schedule.csv has one row per segment: mo,sequence,work_center,start,end
(YYYY-MM-DD HH:MM). An operation may have several segments (ERPNext splits job cards at shift
ends); every segment must be on the same eligible work centre.

Feasibility (any violation = infeasible schedule, the arm fails that instance):
  coverage   every open (not done) work order scheduled; no unknown or duplicate rows
  machine    work centre is the work order's own or one of its listed alternatives
  calendar   working minutes inside the segments >= the work order's duration
  split      an operation is interrupted only at a shift end: every segment but the last ends
             where the work centre's working time ends (one segment may span nights/weekends)
  release    nothing starts before the export time
  frozen     an in-progress work order keeps its work centre and its recorded start
  capacity   no two work orders overlap in wall time on one work centre (capacity 1)
  precedence an operation starts no earlier than the previous operation's last segment ends
Scores: late orders (completion > due), total tardiness (wall hours), makespan (hours from export).
With --base-schedule: work orders moved (work centre changed or start shifted >= 15 min) among
work orders that are still movable in this export.
"""
import argparse
import csv
import datetime as dt
import json
import os
import sys

EPOCH = dt.datetime(2026, 11, 2)
DAYS = 63


def parse_t(s):
    s = s.strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return int((dt.datetime.strptime(s, fmt) - EPOCH).total_seconds() // 60)
        except ValueError:
            pass
    raise ValueError("bad time %r" % s)


def rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def working_mask(data, wc_row):
    """One bool per minute of the horizon: True where the work centre works."""
    mask = bytearray(DAYS * 1440)
    for c in rows(os.path.join(data, "calendars.csv")):
        if c["calendar"] != wc_row["calendar"]:
            continue
        h1, m1 = map(int, c["start"].split(":"))
        h2, m2 = map(int, c["end"].split(":"))
        for day in range(DAYS):
            if (EPOCH + dt.timedelta(days=day)).weekday() == int(c["weekday"]):
                base = day * 1440
                for m in range(base + h1 * 60 + m1, base + h2 * 60 + m2):
                    mask[m] = 1
    for o in rows(os.path.join(data, "time_off.csv")):
        if o["work_center"] in ("ALL", wc_row["work_center"]):
            for m in range(max(parse_t(o["from"]), 0), min(parse_t(o["to"]), DAYS * 1440)):
                mask[m] = 0
    return mask


def check(data, schedule, base=None):
    wcs = {r["work_center"]: r for r in rows(os.path.join(data, "work_centers.csv"))}
    orders = {r["mo"]: r for r in rows(os.path.join(data, "orders.csv"))}
    wos = {(r["mo"], int(r["sequence"])): r for r in rows(os.path.join(data, "work_orders.csv"))}
    now = parse_t(rows(os.path.join(data, "export_info.csv"))[0]["exported_at"])
    masks = {wc: working_mask(data, r) for wc, r in wcs.items()}
    errs = []

    segs = {}
    for i, r in enumerate(rows(schedule)):
        key = (r["mo"].strip(), int(float(r["sequence"])))
        try:
            a, b = parse_t(r["start"]), parse_t(r["end"])
        except ValueError as e:
            errs.append("row %d: %s" % (i + 2, e))
            continue
        if key not in wos:
            errs.append("row %d: unknown work order %s/%s" % (i + 2, *key))
            continue
        if b <= a:
            errs.append("row %d: end <= start" % (i + 2))
            continue
        segs.setdefault(key, []).append((a, b, r["work_center"].strip()))

    for key, w in wos.items():
        if w["state"] == "done":
            segs.pop(key, None)  # done work needs no slot; ignore if an arm repeats it
            continue
        if key not in segs:
            errs.append("coverage: %s/%d not scheduled" % key)
            continue
        ss = sorted(segs[key])
        wcset = {s[2] for s in ss}
        allowed = {w["work_center"]} | {x for x in wcs[w["work_center"]]["alternatives"].split(";") if x}
        if len(wcset) != 1 or not wcset <= allowed:
            errs.append("machine: %s/%d on %s, allowed %s" % (*key, sorted(wcset), sorted(allowed)))
            continue
        wc = ss[0][2]
        for (a1, b1, _), (a2, b2, _) in zip(ss, ss[1:]):
            if a2 < b1:
                errs.append("segments overlap: %s/%d" % key)
        for a, b, _ in ss[:-1]:
            if not (0 < b < DAYS * 1440 and masks[wc][b - 1] and not masks[wc][b]):
                errs.append("split: %s/%d interrupted mid-shift at minute %d" % (*key, b))
        worked = sum(sum(masks[wc][max(a, 0):min(b, DAYS * 1440)]) for a, b, _ in ss)
        if worked < int(w["duration_min"]):
            errs.append("calendar: %s/%d gets %d working min, needs %s" % (*key, worked, w["duration_min"]))
        if w["state"] == "progress":
            if ss[0][0] != parse_t(w["started_at"]) or wc != w["work_center"]:
                errs.append("frozen: %s/%d moved from %s on %s" % (*key, w["started_at"], w["work_center"]))
        elif ss[0][0] < now:
            errs.append("release: %s/%d starts before export time" % key)

    by_wc = {}
    for key, ss in segs.items():
        for a, b, wc in ss:
            by_wc.setdefault(wc, []).append((a, b, key))
    for wc, lst in by_wc.items():
        lst.sort()
        for (a1, b1, k1), (a2, b2, k2) in zip(lst, lst[1:]):
            if a2 < b1 and k1 != k2:
                errs.append("capacity: %s %s/%d overlaps %s/%d" % (wc, *k1, *k2))

    for (mo, seq), w in wos.items():
        prev = [k for k in wos if k[0] == mo and k[1] < seq]
        if not prev or (mo, seq) not in segs:
            continue
        pk = max(prev, key=lambda k: k[1])
        if wos[pk]["state"] == "done":
            continue
        if pk in segs and min(s[0] for s in segs[(mo, seq)]) < max(s[1] for s in segs[pk]):
            errs.append("precedence: %s/%d starts before %s/%d ends" % (mo, seq, *pk))

    comp = {}
    for (mo, seq), ss in segs.items():
        comp[mo] = max(comp.get(mo, 0), max(s[1] for s in ss))
    late, tard = [], 0
    for mo, o in orders.items():
        if mo not in comp:
            continue
        d = parse_t(o["due"])
        if comp[mo] > d:
            late.append(mo)
            tard += comp[mo] - d
    res = {
        "feasible": not errs,
        "errors": errs[:50],
        "n_errors": len(errs),
        "open_work_orders": sum(1 for w in wos.values() if w["state"] != "done"),
        "late_orders": len(late),
        "late": sorted(late),
        "total_tardiness_h": round(tard / 60, 2),
        "makespan_h": round((max(comp.values()) - now) / 60, 2) if comp else 0,
    }
    if base:
        bseg = {}
        for r in rows(base):
            k = (r["mo"].strip(), int(float(r["sequence"])))
            a = parse_t(r["start"])
            if k not in bseg or a < bseg[k][0]:
                bseg[k] = (a, r["work_center"].strip())
        moved = 0
        movable = 0
        for k, w in wos.items():
            if w["state"] in ("done", "progress") or k not in segs or k not in bseg:
                continue
            movable += 1
            a = min(s[0] for s in segs[k])
            if segs[k][0][2] != bseg[k][1] or abs(a - bseg[k][0]) >= 15:
                moved += 1
        res["moved"] = moved
        res["movable"] = movable
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--schedule", required=True)
    ap.add_argument("--base-schedule")
    ap.add_argument("--json")
    a = ap.parse_args()
    res = check(a.data, a.schedule, a.base_schedule)
    if a.json:
        with open(a.json, "w") as f:
            json.dump(res, f, indent=1)
    print("%s late=%d tardiness_h=%.2f makespan_h=%.2f%s errors=%d" % (
        "FEASIBLE" if res["feasible"] else "INFEASIBLE", res["late_orders"], res["total_tardiness_h"],
        res["makespan_h"], (" moved=%d/%d" % (res["moved"], res["movable"])) if "moved" in res else "",
        res["n_errors"]))
    for e in res["errors"][:10]:
        print("  " + e)
    sys.exit(0 if res["feasible"] else 1)


if __name__ == "__main__":
    main()
