"""Load the dataset into a fresh Odoo 20 database as a small shop would have it at export time.

Run inside `odoo shell -d DB` (stdin) with libfaketime preloaded and SHOP_DATA=<dataset base dir>.
All times are UTC (company, admin user and work centres use UTC).

1. Settings: Work Orders (mrp.group_mrp_routings) on.
2. Calendars: the stock "Work Center 40 hours/week" (Mon-Fri 08-16) and a two-shift Mon-Fri 06-22
   calendar; plant shutdown from time_off.csv as a global time off on both.
3. Work centres with their codes, calendars and alternatives (setup/cleanup 0, efficiency 100%).
4. Products and BoMs with one operation per routing row (minutes per unit; no components).
5. 72 MOs with their names, scheduled date (= creation), deadline and star, confirmed in name
   order. Each work order's expected duration is set to the export's value.
6. Floor state, acted out with the clock: the done first operations are started and finished on the
   last working day before the export (Fri, back to back on the saw); the started operations are
   started at the export time (Mon 08:00).
"""
import csv
import datetime as dt
import os
import sys

sys.path.insert(0, os.environ.get("KIT", "/kit"))
from clock import set_clock  # noqa: E402

D = os.environ["SHOP_DATA"]
T = lambda s: dt.datetime.strptime(s, "%Y-%m-%d %H:%M")  # noqa: E731


def rows(name):
    with open(os.path.join(D, name), newline="") as f:
        return list(csv.DictReader(f))


export_at = T(rows("export_info.csv")[0]["exported_at"])
orders = rows("orders.csv")
wos = rows("work_orders.csv")
created_max = max(T(o["created"]) for o in orders)
set_clock(created_max)

admin = env.ref("base.user_admin")  # noqa: F821
e = env(user=admin)  # noqa: F821
admin.write({"tz": "UTC", "password": "admin"})
e.company.write({"tz": "UTC"}) if "tz" in e.company._fields else None
e["res.config.settings"].create({"group_mrp_routings": True}).execute()

# calendars
cal40 = e.ref("mrp.mrp_workcenter_calendar")
cal_rows = rows("calendars.csv")
cals = {}
for code in sorted({c["calendar"] for c in cal_rows}):
    att = [c for c in cal_rows if c["calendar"] == code]
    hours = lambda s: int(s[:2]) + int(s[3:]) / 60  # noqa: E731
    cmds = [(5, 0, 0)] + [(0, 0, {"dayofweek": c["weekday"],
                                  "hour_from": hours(c["start"]), "hour_to": hours(c["end"]),
                                  "duration_hours": hours(c["end"]) - hours(c["start"])}) for c in att]
    if att[0]["name"] == cal40.name:
        cal = cal40
    else:
        cal = e["resource.calendar"].create({"name": att[0]["name"], "company_id": False})
    vals = {"attendance_ids": cmds}
    if "tz" in cal._fields:
        vals["tz"] = "UTC"
    cal.write(vals)
    cals[code] = cal
for off in rows("time_off.csv"):
    for cal in cals.values():
        e["resource.calendar.leaves"].create({"name": off["reason"], "calendar_id": cal.id,
                                              "date_from": T(off["from"]), "date_to": T(off["to"])})

# work centres
wcs = {}
wc_rows = rows("work_centers.csv")
for w in wc_rows:
    wcs[w["work_center"]] = e["mrp.workcenter"].create({
        "name": w["name"], "code": w["work_center"], "resource_calendar_id": cals[w["calendar"]].id,
        "time_efficiency": 100, "time_start": 0, "time_stop": 0, "tz": "UTC"})
for w in wc_rows:
    alts = [a for a in w["alternatives"].split(";") if a]
    if alts:
        wcs[w["work_center"]].alternative_workcenter_ids = [(6, 0, [wcs[a].id for a in alts])]

# products, one BoM per MO and the MOs. Each MO's BoM is sized to its batch (BoM qty = MO qty) and each
# operation's time is that order's duration, so Odoo's own duration formula gives the dataset duration on
# any work centre. Plan recomputes duration_expected when it moves an operation to an alternative work
# centre, so a duration written on the work order would not survive Plan (seen in an earlier load).
routing = rows("routings.csv")
dur = {(w["mo"], int(w["sequence"])): float(w["duration_min"]) for w in wos}
tmpls = {prod: e["product.template"].create({"name": prod, "type": "consu", "is_storable": True})
         for prod in sorted({r["product"] for r in routing} | {o["product"] for o in orders})}
mos = {}
for o in sorted(orders, key=lambda o: o["mo"]):
    tmpl, qty = tmpls[o["product"]], float(o["qty"])
    ops = [r for r in routing if r["product"] == o["product"]]
    bom = e["mrp.bom"].create({
        "product_tmpl_id": tmpl.id, "product_qty": qty, "type": "normal", "code": o["mo"],
        "operation_ids": [(0, 0, {"name": r["operation"], "sequence": int(r["sequence"]),
                                  "workcenter_id": wcs[r["work_center"]].id, "time_mode": "manual",
                                  "time_cycle_manual": dur[(o["mo"], int(r["sequence"]))]}) for r in ops]})
    mo = e["mrp.production"].create({
        "name": o["mo"], "product_id": tmpl.product_variant_id.id, "bom_id": bom.id,
        "product_qty": qty, "date_start": T(o["created"]), "date_deadline": T(o["due"]),
        "priority": o["priority"]})
    mo.action_confirm()
    assert mo.name == o["mo"] and mo.state == "confirmed", (mo.name, mo.state)
    mos[o["mo"]] = mo
wo_of = {}
for w in wos:
    mo = mos[w["mo"]]
    wo = mo.workorder_ids.filtered(lambda x: x.operation_id.sequence == int(w["sequence"]))
    assert len(wo) == 1 and wo.workcenter_id.code == w["work_center"], (w, wo)
    assert abs(wo.duration_expected - float(w["duration_min"])) < 0.005, (w, wo.duration_expected)
    for alt in wo.workcenter_id.alternative_workcenter_ids:  # what Plan would use on the alternative
        assert abs(wo._get_duration_expected(alternative_workcenter=alt) - float(w["duration_min"])) < 0.005, (w, alt.code)
    wo_of[(w["mo"], int(w["sequence"]))] = wo
assert sum(len(m.workorder_ids) for m in mos.values()) == len(wos)
e.cr.commit()

# floor state: done operations on the last working day before the export, back to back on their
# work centre in MO order; then the started operations at the export time
fri = export_at - dt.timedelta(days=3)
cursor = {}
for w in sorted([w for w in wos if w["state"] == "done"], key=lambda w: (w["mo"], int(w["sequence"]))):
    wo = wo_of[(w["mo"], int(w["sequence"]))]
    start = max(cursor.get(w["work_center"], fri), T(next(o for o in orders if o["mo"] == w["mo"])["created"]))
    end = start + dt.timedelta(minutes=float(w["duration_min"]))
    set_clock(start)
    wo.button_start()
    set_clock(end)
    wo.button_finish()
    assert wo.state == "done", wo.state
    cursor[w["work_center"]] = end
    print("done   %s %s %s %s-%s" % (w["mo"], w["sequence"], w["work_center"], start, end.time()))
set_clock(export_at)
for w in [w for w in wos if w["state"] == "progress"]:
    assert T(w["started_at"]) == export_at
    wo = wo_of[(w["mo"], int(w["sequence"]))]
    wo.button_start()
    assert wo.state == "progress", wo.state
    print("start  %s %s %s %s" % (w["mo"], w["sequence"], w["work_center"], export_at))
e.cr.commit()
print("LOADED mos=%d wos=%d done=%d progress=%d" % (
    len(mos), len(wos), e["mrp.workorder"].search_count([("state", "=", "done")]),
    e["mrp.workorder"].search_count([("state", "=", "progress")])))
