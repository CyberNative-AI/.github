# Rerun: Odoo 20 Plan follows the list order

One command builds a container with Odoo 20.0 Community and PostgreSQL 16, loads a 72-order
furniture shop into a fresh database, plans every open manufacturing order twice and prints how
many orders finish after their deadline each time:

- **default**: the Manufacturing Orders list as a fresh user sees it, select all, Plan.
- **deadline**: the same list after clicking the Deadline column header once, select all, Plan.

Needs Docker, about 4 GB of disk and network for the image build (the run itself is offline).

```sh
./rerun.sh
```

Expected last lines:

```
plan from            late MOs      tardiness (h)
default                    20             2125.0
deadline                    0                0.0
```

`ARMS="default deadline deadline_id deadline_id_desc" ./rerun.sh` adds the Deadline sort with its
ties broken by order id, ascending and descending.

## What it does

| file | role |
|---|---|
| `construct.py` | writes the dataset (`data/`): seeded, standard library only, byte-reproducible; the run checks its output against `data/` |
| `Dockerfile` | official `odoo` image (pinned by digest, Odoo Server 20.0-20261015) + PostgreSQL 16 + libfaketime |
| `rerun.sh` | builds the image and runs `inside.sh` with `--network none`; results go to `out/` |
| `inside.sh` | creates the database, installs Manufacturing, loads the shop, then plans and scores each arm |
| `shop_load.py` | loads `data/` through Odoo's own models: calendars (with the Thanksgiving closure), 10 work centres with alternatives, products, one bill of materials per order, 72 confirmed orders with deadlines and stars, then the floor state (8 first operations done on Friday, 3 started Monday 08:00) |
| `plan.py` | the two calls the list makes: read the rows in the list's sort, then `button_plan` with the selected ids in that order |
| `export_plan.py` | writes Odoo's planned work orders as `out/<arm>.csv` |
| `checker.py` | independent schedule checker (standard library only): counts late orders and total tardiness, and lists any rule a schedule breaks |

Odoo's clock is frozen at the dataset's export time, Monday 2026-11-02 08:00 UTC, because Plan
schedules from "now". Times are UTC throughout.

## Construction rule

`construct.py` was written and its output frozen before Odoo planned anything.

- Shop: 10 work centres. CNC Router A runs two shifts (06:00 to 22:00) with CNC Router B (one shift)
  as its alternative; Assembly 1 and Assembly 2 are alternatives; the Paint Booth is the bottleneck.
  The plant is closed for Thanksgiving, November 26 and 27.
- 72 open manufacturing orders, 347 work orders, routings of 3 to 6 operations. Duration = setup +
  quantity x minutes per unit, rounded up to 15 minutes.
- Deadlines in working days from the export time (Monday 2026-11-02 08:00), drawn with chance
  25% in 1 to 3 days, 50% in 4 to 9 and 25% in 10 to 15, never earlier than the order's own work at
  8 hours a day. Each order is starred with chance 10%; the seed gives 4 starred orders.
- Floor state at export: 8 orders have their first operation done; 3 operations started at 08:00.
- Orders are numbered in creation order, which is not deadline order.
- `data/slips.json` holds three disruptions (a paint booth stop, a 4-hour overrun, a rush order)
  that this rerun does not use.

## Reading the checker output

`out/<arm>.check.txt` starts with `INFEASIBLE ... errors=17` for both arms. That is Odoo's
behaviour, not a loading problem: for 7 of the 8 orders whose first operation was finished on
Friday (the eighth already has its second operation started), Plan books the next operations
straight after it, which is before Monday 08:00, and the checker counts
any work booked before the export time as an error (and the minutes before Monday 00:00 as
non-working, hence a few "calendar" lines). The late counts are unaffected.

## Licences

The scripts are MIT-licensed (`LICENSE`). Parts of the dataset derive from Odoo's
LGPL-3 demo data; see `NOTICE-LGPL-3.md`.
