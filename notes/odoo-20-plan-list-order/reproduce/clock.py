"""Move libfaketime's clock for this process (FAKETIME_TIMESTAMP_FILE + FAKETIME_NO_CACHE=1)."""
import datetime as dt
import os

FILE = os.environ.get("FAKETIME_TIMESTAMP_FILE")


def set_clock(when):
    """Freeze the process clock at `when` (naive UTC datetime) and check that it took."""
    with open(FILE, "w") as f:
        f.write(when.strftime("%Y-%m-%d %H:%M:%S") + "\n")
    now = dt.datetime.now().replace(microsecond=0)
    if now != when:
        raise SystemExit("fake clock not applied: wanted %s, process sees %s" % (when, now))
