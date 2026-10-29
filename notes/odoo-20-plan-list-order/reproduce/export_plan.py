"""Export Odoo's planned work orders in the checker's schedule format, plus an MO summary.

Run inside `odoo shell -d DB` with OUT=<prefix>. Writes <prefix>.csv (mo,sequence,work_center,start,end;
open work orders only, done ones are history) and <prefix>.mos.csv (what the MO list holds).
"""
import csv
import os

out = os.environ["OUT"]
e = env  # noqa: F821
import datetime as dt
fmt = lambda d: d.strftime("%Y-%m-%d %H:%M:%S") if d else ""  # noqa: E731
# checker/slipstate read minutes; Odoo keeps seconds. Round to the minute and count what moved.
rounded = []


def fmin(d):
    if not d:
        return ""
    r = (d + dt.timedelta(seconds=30)).replace(second=0, microsecond=0)
    if r != d.replace(microsecond=0):
        rounded.append(fmt(d))
    return r.strftime("%Y-%m-%d %H:%M")
wos = e["mrp.workorder"].search([("state", "not in", ("done", "cancel"))])
with open(out + ".csv", "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["mo", "sequence", "work_center", "start", "end"])
    for wo in sorted(wos, key=lambda x: (x.production_id.name, x.operation_id.sequence)):
        w.writerow([wo.production_id.name, wo.operation_id.sequence, wo.workcenter_id.code,
                    fmin(wo.date_start), fmin(wo.date_finished)])
with open(out + ".raw.csv", "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["mo", "sequence", "work_center", "state", "start", "end", "duration_expected"])
    for wo in sorted(e["mrp.workorder"].search([]), key=lambda x: (x.production_id.name, x.operation_id.sequence)):
        w.writerow([wo.production_id.name, wo.operation_id.sequence, wo.workcenter_id.code, wo.state,
                    fmt(wo.date_start), fmt(wo.date_finished), wo.duration_expected])
mos = e["mrp.production"].search([])
with open(out + ".mos.csv", "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["id", "mo", "priority", "state", "is_planned", "date_start", "date_finished",
                "date_deadline", "is_delayed"])
    for m in mos:  # default _order: the order a fresh MO list shows
        w.writerow([m.id, m.name, m.priority, m.state, m.is_planned, fmt(m.date_start),
                    fmt(m.date_finished), fmt(m.date_deadline), m.is_delayed])
print("EXPORTED %d work orders, %d MOs -> %s; %d timestamps rounded to the minute %s" % (
    len(wos), len(mos), out, len(rounded), rounded[:3]))
