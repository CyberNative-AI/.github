"""Count records on clock-reset ("sentinel") dates.

  python3 sentinel_dates.py gbif [--dataset KEY]
      Ask the GBIF occurrence API how many records fall on each sentinel date, and compare
      with nearby days in the same year and the same day in nearby years. About 250 requests,
      at most 4 per second; it takes a few minutes. No login.

  python3 sentinel_dates.py clock [--dataset KEY]
      Read every record on 1980-01-01 and 2000-01-01 and on the days around them, and count
      how many have a clock time of 00:00-00:19. Also prints the commonest hours on the two
      Unix dates. About 60 requests.

  python3 sentinel_dates.py file DOWNLOAD.tsv [--exclude-to CLEAN.tsv] [--dates 1980-01-01,...] [--midnight]
      Count the rows of a GBIF download (simple CSV or the occurrence.txt of a Darwin Core
      Archive, both tab-separated) that fall on a sentinel date. With --exclude-to, write
      every other row, unchanged, to a new file (an existing file is never overwritten).
      Genuine records on these dates are excluded too.
      With --midnight, rows on 1980-01-01 and 2000-01-01 count only if their clock time
      is 00:00-00:19.

Standard library only.
"""

import argparse
import contextlib
import json
import re
import statistics
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, timedelta

# date -> where the value comes from
SENTINELS = {
    date(1899, 11, 30): "day 0 of month 0",
    date(1899, 12, 30): "Excel/Access zero date (OLE)",
    date(1899, 12, 31): "Excel 1900 system, day 0",
    date(1900, 1, 1): "Excel 1900 system, day 1",
    date(1904, 1, 1): "Mac/Excel 1904 system",
    date(1969, 12, 31): "Unix time 0, west of UTC",
    date(1970, 1, 1): "Unix time 0, UTC and east",
    date(1980, 1, 1): "DOS/FAT timestamp zero",
    date(1980, 1, 6): "GPS week 0",
    date(2000, 1, 1): "common camera clock reset",
    date(2000, 12, 31): "Apple reference date, west of UTC",
    date(2001, 1, 1): "Apple reference date, UTC and east",
}
# Dates with an excess in our 16 October 2026 measurement (iNaturalist or GBIF); the default for `file`.
DEFAULT_FILE_DATES = [date(1899, 11, 30), date(1899, 12, 30), date(1899, 12, 31), date(1900, 1, 1),
                      date(1969, 12, 31), date(1970, 1, 1), date(1980, 1, 1), date(2000, 1, 1)]
INAT_RESEARCH_GRADE = "50c9509d-22c7-4a22-a47d-8c48425ef4a7"
DATE_ISSUES = {"RECORDED_DATE_MISMATCH", "RECORDED_DATE_INVALID", "RECORDED_DATE_UNLIKELY"}
API = "https://api.gbif.org/v1/occurrence/search"
MIDNIGHT_DATES = {date(1980, 1, 1), date(2000, 1, 1)}
CLOCK = re.compile(r"T(\d{2}):(\d{2})")


def nearby_days(d):
    """The same year, 1-7 days either side, skipping other sentinel dates."""
    out = [d + timedelta(days=s * k) for k in range(1, 8) for s in (-1, 1)]
    return sorted(c for c in out if c not in SENTINELS)


def same_day_other_years(d):
    """The same calendar day 1-3 years either side, skipping other sentinel dates."""
    out = [date(d.year + k, d.month, d.day) for k in (-3, -2, -1, 1, 2, 3)]
    return sorted(c for c in out if c not in SENTINELS)


_last = [0.0]


def gbif_get(params):
    url = API + "?" + urllib.parse.urlencode(params)
    time.sleep(max(0.0, _last[0] + 0.25 - time.monotonic()))
    _last[0] = time.monotonic()
    req = urllib.request.Request(url, headers={"User-Agent": "sentinel_dates.py", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def gbif_day(d, dataset):
    """(record count, records carrying a GBIF date issue flag, upper bound) for one day."""
    params = {"eventDate": d.isoformat(), "limit": 0, "facet": "issue", "facetLimit": 100}
    if dataset:
        params["datasetKey"] = dataset
    body = gbif_get(params)
    flagged = sum(c["count"] for f in body.get("facets", []) if f["field"] == "ISSUE"
                  for c in f["counts"] if c["name"] in DATE_ISSUES)
    return body["count"], flagged


def cmd_gbif(args):
    dataset = None if args.dataset == "all" else args.dataset
    print(f"GBIF occurrence API, dataset {args.dataset}, read {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}")
    print("date        records  nearby  other-yrs  ratio  excess  date-flagged  source")
    total = 0
    for d, origin in SENTINELS.items():
        n, flagged = gbif_day(d, dataset)
        a = statistics.median(gbif_day(c, dataset)[0] for c in nearby_days(d))
        b = statistics.median(gbif_day(c, dataset)[0] for c in same_day_other_years(d))
        ratio = n / max(a, b, 1)
        excess = n - max(a, b)
        # an excess counts when the day is at least 5x both baselines and at least 20 records above them
        effect = n >= 5 * max(a, 1) and n >= 5 * max(b, 1) and excess >= 20
        total += excess if effect else 0
        mark = "*" if effect else " "
        print(f"{d}  {n:7d}  {a:6g}  {b:9g}  {ratio:5.0f}  {excess:6g}{mark} {flagged:12d}  {origin}")
    print(f"* = at least 5x both baselines and 20 records above them. Excess on those days: {total:g}")
    print("date-flagged is an upper bound: a record with two date issues is counted twice.")


def clock(event_date):
    """(hour, minute) of an eventDate's clock time as written, else None."""
    m = CLOCK.search(event_date or "")
    return (int(m[1]), int(m[2])) if m else None


def is_midnight(event_date):
    c = clock(event_date)
    return c is not None and c[0] == 0 and c[1] < 20


def gbif_event_dates(d, dataset):
    """The eventDate of every record on one day (pages of 300)."""
    out, offset = [], 0
    while True:
        params = {"eventDate": d.isoformat(), "limit": 300, "offset": offset}
        if dataset:
            params["datasetKey"] = dataset
        body = gbif_get(params)
        out += [r.get("eventDate") for r in body["results"]]
        offset += 300
        if body.get("endOfRecords") or offset >= body["count"]:
            return out


def cmd_clock(args):
    dataset = None if args.dataset == "all" else args.dataset
    print(f"GBIF occurrence API, dataset {args.dataset}, read {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}")
    print("Clock time 00:00-00:19 as written in eventDate; 'days around' = same year, 1-7 days either side.")
    print("date        records  at 00:00-00:19   days around: records  at 00:00-00:19   expected genuine")
    selected = genuine = 0
    for d in sorted(MIDNIGHT_DATES):
        day = gbif_event_dates(d, dataset)
        mid = sum(map(is_midnight, day))
        around = [e for c in nearby_days(d) for e in gbif_event_dates(c, dataset)]
        around_mid = sum(map(is_midnight, around))
        share = around_mid / len(around) if around else 0.0
        exp = len(day) * share
        selected, genuine = selected + mid, genuine + exp
        print(f"{d}  {len(day):7d}  {mid:6d} ({mid / max(len(day), 1):5.1%})"
              f"   {len(around):20d}  {around_mid:6d} ({share:5.1%})   {exp:16.0f}")
    print(f"Both dates, clock 00:00-00:19: {selected} records; about {genuine:.0f} "
          f"({genuine / max(selected, 1):.1%}) expected genuine at the days-around rate.")
    print("Unix dates, commonest clock hours as written:")
    for d in (date(1969, 12, 31), date(1970, 1, 1)):
        day = gbif_event_dates(d, dataset)
        hours = Counter(c[0] for c in map(clock, day) if c)
        top = ", ".join(f"{h:02d}h {n}" for h, n in hours.most_common(4))
        print(f"{d}  {len(day):7d} records, {sum(hours.values())} with a time: {top}")


def row_date(row, col):
    """The single day a row's eventDate names, else None (ranges and partial dates are skipped)."""
    v = row[col["eventDate"]] if "eventDate" in col and col["eventDate"] < len(row) else ""
    if v:
        start, _, end = v.partition("/")
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", start)
        if not m or (end and end[:10] != start[:10]):
            return None
        return date(int(m[1]), int(m[2]), int(m[3]))
    try:
        return date(int(row[col["year"]]), int(row[col["month"]]), int(row[col["day"]]))
    except (KeyError, ValueError, IndexError):
        return None


def cmd_file(args):
    dates = ([date.fromisoformat(s) for s in args.dates.split(",")] if args.dates else DEFAULT_FILE_DATES)
    wanted = set(dates)
    hits, by_dataset, rows = Counter(), Counter(), 0
    with contextlib.ExitStack() as stack:
        # GBIF downloads are tab-separated without quoting: one record per line. Lines are split
        # to read the date and copied unchanged, so retained rows keep every byte.
        f = stack.enter_context(open(args.path, encoding="utf-8", newline=""))
        header_line = f.readline()
        col = {name: i for i, name in enumerate(header_line.rstrip("\r\n").split("\t"))}
        if "eventDate" not in col and not {"year", "month", "day"} <= col.keys():
            sys.exit("no eventDate or year/month/day column: is this a GBIF download?")
        out = None
        if args.exclude_to:
            try:  # "x": never overwrite an existing file, including the download itself
                out = stack.enter_context(open(args.exclude_to, "x", encoding="utf-8", newline=""))
            except FileExistsError:
                sys.exit(f"{args.exclude_to} already exists; give a new file name")
            out.write(header_line)
        for line in f:
            if not line.strip("\r\n"):
                continue
            rows += 1
            row = line.rstrip("\r\n").split("\t")
            d = row_date(row, col)
            if d in wanted and args.midnight and d in MIDNIGHT_DATES:
                hit = is_midnight(row[col["eventDate"]] if "eventDate" in col else "")
            else:
                hit = d in wanted
            if hit:
                hits[d] += 1
                if "datasetKey" in col and col["datasetKey"] < len(row):
                    by_dataset[row[col["datasetKey"]]] += 1
            elif out:
                out.write(line)
    rule = " (1980-01-01 and 2000-01-01: clock 00:00-00:19 only)" if args.midnight else ""
    print(f"{rows} rows, {sum(hits.values())} on a sentinel date{rule}")
    for d in dates:
        print(f"  {d}  {hits[d]:8d}  {SENTINELS.get(d, '')}")
    if by_dataset:
        print("by datasetKey (top 5):")
        for k, v in by_dataset.most_common(5):
            print(f"  {k}  {v}")
    if args.exclude_to:
        print(f"wrote the other {rows - sum(hits.values())} rows to {args.exclude_to}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gbif", help="count sentinel dates through the GBIF API")
    g.add_argument("--dataset", default=INAT_RESEARCH_GRADE,
                   help="GBIF datasetKey, or 'all' (default: iNaturalist research-grade observations)")
    f = sub.add_parser("file", help="count sentinel dates in a GBIF download")
    f.add_argument("path")
    f.add_argument("--exclude-to", help="write the rows that are not on a sentinel date to this new file")
    f.add_argument("--dates", help="comma-separated dates instead of the default list")
    f.add_argument("--midnight", action="store_true",
                   help="on 1980-01-01 and 2000-01-01, count only rows with a clock time of 00:00-00:19")
    c = sub.add_parser("clock", help="clock times on 1980-01-01 and 2000-01-01 through the GBIF API")
    c.add_argument("--dataset", default=INAT_RESEARCH_GRADE,
                   help="GBIF datasetKey, or 'all' (default: iNaturalist research-grade observations)")
    args = p.parse_args()
    {"gbif": cmd_gbif, "file": cmd_file, "clock": cmd_clock}[args.cmd](args)


if __name__ == "__main__":
    main()
