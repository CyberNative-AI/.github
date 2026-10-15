"""Historical collection script (network). It documents how the evidence was collected; the supported
operation for this bundle is the offline recompute in RESULT.md. Its download and time limits are not enforced
(see the correction in PROTOCOL.md section 7): run it only under disk, memory and wall-time limits applied
outside the script.

Fetch every recent-changes row (edit/new/log) in the frozen window W for one wiki (timing control).

usage: rcfetch.py WIKI
Writes evidence/rc/<wiki>.json: {api, count, rows:[{type,title,pageid,revid,old_revid,timestamp,logtype,logaction,target}]}.
Recent changes keep ~30 days, so W (2026-09-28..10-08) must be fetched before ~2026-10-27.
"""
from __future__ import annotations

import gzip
import json
import sys
import time
import urllib.parse

from common import EVID, INPUTS, W_END, W_START, http_get, write_json


def api_url(wiki: str) -> str:
    with gzip.open(INPUTS / "sitematrix.json.gz", "rt", encoding="utf-8") as f:
        sm = json.load(f)["sitematrix"]
    for k, v in sm.items():
        if k == "count":
            continue
        for s in (v if k == "specials" else v["site"]):
            if s["dbname"] == wiki:
                return s["url"] + "/w/api.php"
    raise KeyError(wiki)


def api(base: str, params: dict) -> dict:
    q = {"format": "json", "formatversion": "2", "maxlag": "5", **params}
    for i in range(6):
        d = json.loads(http_get(base + "?" + urllib.parse.urlencode(q)))
        if d.get("error", {}).get("code") == "maxlag":
            time.sleep(10 * (i + 1))
            continue
        if "error" in d:
            raise RuntimeError(f"API error {d['error']}")
        time.sleep(1)
        return d
    raise RuntimeError("maxlag persisted")


def main(wiki: str) -> int:
    base = api_url(wiki)
    rows = []
    p = {"action": "query", "list": "recentchanges", "rcstart": W_END, "rcend": W_START, "rcdir": "older",
         "rcprop": "title|ids|timestamp|loginfo", "rctype": "edit|new|log", "rclimit": "500"}
    cont = {}
    while True:
        d = api(base, {**p, **cont})
        for r in d["query"]["recentchanges"]:
            lp = r.get("logparams") or {}
            rows.append({"type": r["type"], "title": r.get("title"), "pageid": r.get("pageid"), "revid": r.get("revid"),
                         "old_revid": r.get("old_revid"), "timestamp": r.get("timestamp"),
                         "logtype": r.get("logtype"), "logaction": r.get("logaction"),
                         "target": lp.get("target_title")})
        if "continue" not in d:
            break
        cont = d["continue"]
    oldest = api(base, {"action": "query", "list": "recentchanges", "rcdir": "newer", "rclimit": "1", "rcprop": "timestamp"})
    first = (oldest["query"]["recentchanges"] or [{}])[0].get("timestamp")
    write_json(EVID / "rc" / f"{wiki}.json", {"api": base, "window": [W_START, W_END], "count": len(rows),
                                              "oldest_rc": first, "covers_window": first is None or first <= W_START,
                                              "rows": rows})
    print(json.dumps({"wiki": wiki, "rc_rows": len(rows), "oldest_rc": first}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
