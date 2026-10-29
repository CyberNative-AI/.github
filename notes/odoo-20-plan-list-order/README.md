# Odoo 20 plans manufacturing orders in the order the list shows them

Odoo 20's release notes say it under Manufacturing: "Manufacturing orders are now planned as soon as possible by default. When multiple orders are planned, their sequence in the list determines scheduling priority." ([Odoo 20 release notes](https://www.odoo.com/odoo-20-release-notes))

We loaded a 72-order, 10-work-centre shop into Odoo 20.0 Community and pressed Plan on all of its orders twice, each time on its own copy of the same loaded database:

| Plan from | Orders finishing after their deadline | Total lateness |
|---|---|---|
| The Manufacturing Orders list as it first opens | 20 | 2,125.0 h |
| The same list after one click on the Deadline column header | 0 | 0.0 h |

The orders, machines, calendars and button are the same in both runs. Only the row order differs.

## What we checked

- **Plan follows the displayed order.** In a browser, selecting all rows and pressing Plan sent all 72 order ids to the server in exactly the order the list showed, for both sorts. All 72 fit on one 80-row page.
- **"Select all" drops the sort.** On a list longer than one page, the header checkbox offers "Select all" for the rest. With the same 72 orders spread over two pages and the list sorted by Deadline, that option sent the ids in Odoo's default order, and the plan came out identical to the one from the default list: 20 late. Showing every order on one page first (page counter set to 1-500), then the header checkbox, left 0 late.
- **The default list is not sorted by deadline.** It opens on the "To Do" filter with no sorted column: starred orders first, then by Start. The Deadline column is hidden by default; it is an optional column in the column toggle at the right of the header row.
- **Ties do not change the result.** 70 of the 72 orders share a deadline with at least one other order. The Deadline-sorted plan still leaves 0 late when ties are broken by order id in either direction.
- **Odoo's own late markers agree.** After the default-order plan, the "Late" filter, the "Delayed Productions" filter and the red Deadline text each show the same 20 orders that our independent checker counts.

## What to do before you press Plan

1. Open Manufacturing. It starts on Operations > Manufacturing Orders.
2. Turn on the Deadline column in the column toggle, then click its header once (earliest first).
3. Tick the header checkbox, then press Plan. With more orders than one page, first type a range that covers them all into the page counter (it reads 1-80), such as 1-500. Don't use "Select all", and don't plan page by page: after a Plan, orders with the same deadline can change places, and one order was never selected in our test.
4. Check the "Late" filter afterwards.

Plan leaves already-planned orders where they are and fits the rest around them. With half the orders planned earlier from the default list, the Deadline sort still left 20 late. To re-plan the whole list, first go to Work Orders, untick "In Progress" in the filter menu so only "To Do" and "Blocked" remain, tick the header checkbox, then "Select all" (fine here: the order you unplan in doesn't matter), and choose Actions > Unplan. Then follow steps 1-4 above; that left 0 late. Unplanning started work orders instead left 3 running orders with no dates.

If you rely on stars: planning the starred orders first and the rest afterwards left the starred orders' work orders where the first Plan put them (0 of 22 moved).

## Two more things the same run showed

These come from the same Odoo run. The rerun kit below does not include them.

- **Plan can book work in the past.** For 7 orders whose first operation was finished on the Friday before, Plan booked the next operation straight after it, before the Monday "now", instead of moving it forward.
- **Odoo moves nothing when an operation runs long.** After one operation was recorded 4 working hours over, its order's next operation stayed booked to start before the long one ended. Unplanning the unstarted work orders and pressing Plan again repeated the pattern: from the default list, 20 orders stayed late; from the Deadline-sorted list, 0. Community 20.0 shows no Replan button.

## Rerun it

[`reproduce/`](reproduce/) holds the dataset construction, the loader, the two Plan calls, an independent schedule checker and one command, `./rerun.sh`, that builds a container (official `odoo` image pinned by digest, PostgreSQL 16, libfaketime), runs offline and prints the late counts for both sorts. Its README lists every file, the construction rule and how to read the checker output.

## Limits

- One build: Odoo Server 20.0-20261015, official Docker Hub image `sha256:61e3c71b0503c5f658e604c3e340bede20b97d05f726179fa006eae50a32fd23`, Community edition, run October 29, 2026. Plan's code (`button_plan`, `_plan_workorders`, `action_replan`) is identical on the 20.0 branch as of October 28; some calendar code differs there and we did not rerun on it. We did not test Enterprise or 19.0.
- One synthetic shop, partly derived from Odoo's demo data: 72 orders, 347 work orders, deadlines 1 to 15 working days out, 4 starred orders, Odoo's clock frozen at Monday 2026-11-02 08:00 UTC.
- The gap needs orders that sit in the list out of deadline order. Here they were entered over two weeks with deadlines unrelated to entry order. A shop whose orders arrive roughly in deadline order should expect a smaller difference.
- Lateness counts the planned finish against the deadline. Nothing was produced.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai.
