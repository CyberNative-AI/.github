"""Plan every open manufacturing order the way the MO list's Plan button does.

The list asks the server for its rows (web_search_read with the list's sort), the user selects all,
and Plan sends button_plan with the selected ids in the order the list shows them. This script makes
the same two calls. In a browser run on Odoo 20.0 Community, select all + Plan sent exactly these ids
in exactly this order, for both sorts.

  python3 plan.py --db DB [--order "date_deadline ASC"] --log ids.json   (server clock frozen)
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.environ.get("KIT", os.path.dirname(os.path.abspath(__file__))))
from rpc import Odoo  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--db", required=True)
ap.add_argument("--url", default="http://127.0.0.1:8069")
ap.add_argument("--order", default="", help='"" = the default list; "date_deadline ASC" = Deadline header clicked')
ap.add_argument("--log", required=True)
a = ap.parse_args()
o = Odoo(a.url, a.db)
# the MO list's default "To Do" filter
TODO = [("state", "in", ["draft", "confirmed", "progress", "to_close"]), ("picking_type_id.active", "=", True)]
ids = o.list_ids("mrp.production", TODO, a.order)
o.button("mrp.production", "button_plan", ids)
json.dump({"order": a.order, "ids": ids}, open(a.log, "w"))
print("PLANNED", len(ids), "orders, sort %r" % (a.order or "default"))
