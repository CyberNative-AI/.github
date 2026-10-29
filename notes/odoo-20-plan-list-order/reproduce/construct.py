#!/usr/bin/env python3
"""Construct the small-shop MRP dataset: OUTDIR/base/*.csv (the ERP export) and OUTDIR/slips.json.

Written and frozen before any arm ran; see README "Construction rule". Stdlib only, seeded,
byte-reproducible:  python3 construct.py OUTDIR
"""
import csv
import json
import math
import os
import random
import sys

SEED = 2358
N_MO = 72
NOW = "2026-11-02 08:00"  # export time: Monday shift start

# Work centres. Assembly 1, Assembly 2 and Drill 1 and the 40 h/week calendar (Mon-Fri 08-16)
# are Odoo's mrp demo records (addons/mrp/data/mrp_demo.xml, mrp_data.xml); the rest complete a
# furniture job shop around the demo's products.
WORK_CENTERS = [
    # code, name, calendar, alternatives
    ("SAW", "Panel Saw", "C40", ""),
    ("CNC-A", "CNC Router A", "C80", "CNC-B"),
    ("CNC-B", "CNC Router B", "C40", "CNC-A"),
    ("DRL", "Drill 1", "C40", ""),
    ("EDG", "Edge Bander", "C40", ""),
    ("SND", "Sanding", "C40", ""),
    ("PNT", "Paint Booth", "C40", ""),
    ("AS1", "Assembly 1", "C40", "AS2"),
    ("AS2", "Assembly 2", "C40", "AS1"),
    ("PKG", "Testing & Packing", "C40", ""),
]
CALENDARS = {
    "C40": ("Work Center 40 hours/week", [(wd, "08:00", "16:00") for wd in range(5)]),
    "C80": ("Two shifts 80 hours/week", [(wd, "06:00", "22:00") for wd in range(5)]),
}
TIME_OFF = [("ALL", "2026-11-26 00:00", "2026-11-28 00:00", "Thanksgiving plant shutdown")]

# Product routings: (operation, primary work centre, setup minutes, minutes per unit).
# Product names and the Assembly/Long time assembly/Testing/Packing operations come from the demo.
ROUTINGS = {
    "Dining Table": [("Cut", "SAW", 20, 8), ("Rout", "CNC-A", 30, 12), ("Edge band", "EDG", 15, 5),
                     ("Paint", "PNT", 30, 17), ("Assembly", "AS1", 15, 30), ("Packing", "PKG", 10, 8)],
    "Desk": [("Cut", "SAW", 20, 6), ("Rout", "CNC-A", 30, 10), ("Drill", "DRL", 10, 4),
             ("Paint", "PNT", 30, 14), ("Assembly", "AS1", 15, 40), ("Packing", "PKG", 10, 8)],
    "Table Top": [("Cut", "SAW", 15, 6), ("Rout", "CNC-A", 30, 10), ("Edge band", "EDG", 15, 4),
                  ("Sand", "SND", 10, 5), ("Paint", "PNT", 30, 14)],
    "Drawer": [("Cut", "SAW", 15, 3), ("Drill", "DRL", 10, 3), ("Manual Assembly", "AS1", 10, 20),
               ("Packing", "PKG", 5, 4)],
    "Drawer Case Black": [("Cut", "SAW", 15, 4), ("Rout", "CNC-A", 20, 6), ("Paint", "PNT", 30, 11),
                          ("Manual Assembly", "AS1", 10, 25)],
    "Wood Panel": [("Cut", "SAW", 15, 4), ("Sand", "SND", 10, 3), ("Paint", "PNT", 20, 7)],
    "Plastic Laminate": [("Edge band", "EDG", 15, 5), ("Long time assembly", "AS1", 10, 30),
                         ("Testing", "PKG", 10, 10)],
    "Shelf Unit": [("Cut", "SAW", 15, 5), ("Drill", "DRL", 10, 4), ("Edge band", "EDG", 15, 4),
                   ("Sand", "SND", 10, 3), ("Assembly", "AS1", 10, 15)],
}
PRODUCT_WEIGHTS = {"Dining Table": 3, "Desk": 3, "Table Top": 3, "Drawer": 2, "Drawer Case Black": 2,
                   "Wood Panel": 2, "Plastic Laminate": 1, "Shelf Unit": 2}
QTYS = [2, 3, 4, 5, 6, 8, 10, 12]
QTY_WEIGHTS = [3, 3, 4, 3, 3, 2, 2, 1]


def ceil15(x):
    return int(math.ceil(x / 15.0) * 15)


def working_days(start_date_str, n):
    """The n-th Mon-Fri working day after the export day (1 = next working day), skipping TIME_OFF."""
    import datetime as dt
    d = dt.date.fromisoformat(start_date_str[:10])
    shut = {dt.date(2026, 11, 26), dt.date(2026, 11, 27)}
    k = 0
    while k < n:
        d += dt.timedelta(days=1)
        if d.weekday() < 5 and d not in shut:
            k += 1
    return d.isoformat()


def build(out):
    rng = random.Random(SEED)
    base = os.path.join(out, "base")
    os.makedirs(base, exist_ok=True)

    def write(name, header, rows):
        with open(os.path.join(base, name), "w", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(header)
            w.writerows(rows)

    write("export_info.csv", ["exported_at", "note"],
          [[NOW, "Open manufacturing orders and work orders, export from the ERP"]])
    write("work_centers.csv", ["work_center", "name", "calendar", "alternatives"],
          [list(w) for w in WORK_CENTERS])
    write("calendars.csv", ["calendar", "name", "weekday", "start", "end"],
          [[c, nm, wd, a, b] for c, (nm, rows) in CALENDARS.items() for wd, a, b in rows])
    write("time_off.csv", ["work_center", "from", "to", "reason"], [list(t) for t in TIME_OFF])
    write("routings.csv", ["product", "sequence", "operation", "work_center", "setup_min", "minutes_per_unit"],
          [[p, 10 * (i + 1), op, wc, s, u] for p, ops in ROUTINGS.items() for i, (op, wc, s, u) in enumerate(ops)])

    products = list(PRODUCT_WEIGHTS)
    orders, wos = [], []
    for i in range(N_MO):
        mo = "WH/MO/%05d" % (101 + i)
        prod = rng.choices(products, [PRODUCT_WEIGHTS[p] for p in products])[0]
        qty = rng.choices(QTYS, QTY_WEIGHTS)[0]
        ops = [(10 * (k + 1), op, wc, ceil15(s + qty * u)) for k, (op, wc, s, u) in enumerate(ROUTINGS[prod])]
        total = sum(d for *_, d in ops)
        # Due date: working-day offset by class, never earlier than the order's own work at 8 h/day.
        cls = rng.random()
        if cls < 0.25:
            off = rng.randint(1, 3)
        elif cls < 0.75:
            off = rng.randint(4, 9)
        else:
            off = rng.randint(10, 15)
        off = max(off, math.ceil(total / 480.0))
        due = working_days(NOW, off) + " 16:00"
        prio = "1" if rng.random() < 0.10 else "0"
        created = "2026-10-%02d %02d:%02d" % (19 + i * 12 // N_MO, 8 + (i * 7) % 8, (i * 13) % 60)
        orders.append([mo, prod, qty, due, prio, created])
        for seq, op, wc, d in ops:
            wos.append([mo, seq, op, wc, d, "ready", ""])
    # Floor state at export: 8 orders have their first operation done, 3 have one running since 08:00.
    by_mo = {}
    for w in wos:
        by_mo.setdefault(w[0], []).append(w)
    mos = [o[0] for o in orders]
    done_mos = rng.sample(mos, 8)
    for mo in done_mos:
        by_mo[mo][0][5] = "done"
    busy, running = set(), []
    for mo in rng.sample(mos, len(mos)):
        if len(running) == 3:
            break
        ops = by_mo[mo]
        k = 1 if mo in done_mos else 0
        if k >= len(ops) or ops[k][3] in busy:
            continue
        ops[k][5] = "progress"
        ops[k][6] = NOW
        busy.add(ops[k][3])
        running.append(mo)
    for mo, ops in by_mo.items():
        first_open = True
        for w in ops:
            if w[5] in ("done", "progress"):
                continue
            w[5] = "ready" if first_open and (ops.index(w) == 0 or ops[ops.index(w) - 1][5] == "done") else "waiting"
            first_open = False
    write("orders.csv", ["mo", "product", "qty", "due", "priority", "created"], orders)
    write("work_orders.csv", ["mo", "sequence", "operation", "work_center", "duration_min", "state", "started_at"], wos)

    # Slip events (applied to each arm's own base schedule; see README).
    cand = [o[0] for o in orders
            if any(w[3] == "CNC-A" and w[5] in ("ready", "waiting") for w in by_mo[o[0]])
            and "2026-11-06" <= o[3][:10] <= "2026-11-12"]
    over_mo = rng.choice(sorted(cand))
    over_seq = next(w[1] for w in by_mo[over_mo] if w[3] == "CNC-A")
    slips = [
        {"id": "S1", "type": "machine_down", "at": "2026-11-03 10:00", "work_center": "PNT",
         "from": "2026-11-03 10:00", "to": "2026-11-04 12:00",
         "text": "Paint Booth extraction fan failed Tuesday 10:00; booth down until Wednesday 12:00."},
        {"id": "S2", "type": "overrun", "mo": over_mo, "sequence": over_seq, "extra_min": 240,
         "at": "planned_end",
         "text": "At its planned finish, %s operation %d (Rout) needs 4 more working hours (tool breakage)." % (over_mo, over_seq)},
        {"id": "S3", "type": "rush_order", "at": "2026-11-04 13:00", "mo": "WH/MO/%05d" % (101 + N_MO),
         "product": "Dining Table", "qty": 4, "due": "2026-11-06 16:00", "priority": "1",
         "text": "Rush order arrives Wednesday 13:00: 4 Dining Tables due Friday 16:00."},
    ]
    with open(os.path.join(out, "slips.json"), "w") as f:
        json.dump(slips, f, indent=1)
        f.write("\n")


if __name__ == "__main__":
    build(sys.argv[1])
