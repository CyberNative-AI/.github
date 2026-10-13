"""Summarize checkbeam2604.py --json output for a sample of repositories.

usage: python3 sample/summarize.py results.jsonl [head-dates.txt [AS_OF]]
A repository is exposed when it has a setup-beam step on a hosted ubuntu-latest job (any status
but NA). head-dates.txt (from clone.sh: "DIR YYYY-MM-DD" per line) adds the cuts by last commit.
"""
import collections, datetime, json, math, os, sys


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def beam(f):
    return [x for x in f if x["action"] == "setup-beam" and x["status"] != "NA"]


def newly_red(f):
    """A workflow file with a BREAK and no ALREADY entry: everything installs there today."""
    per_file = collections.defaultdict(set)
    for x in beam(f):
        if x["status"] in ("OK", "BREAK", "ALREADY"):
            per_file[x["where"].split(":")[0]].add(x["status"])
    return any("BREAK" in s and "ALREADY" not in s for s in per_file.values())


def cut(rows):
    exp = [r for r in rows if beam(r["findings"])]
    brk = [r for r in exp if any(x["status"] == "BREAK" for x in beam(r["findings"]))]
    unk = [r for r in exp if r not in brk and any(x["status"] == "UNKNOWN" for x in beam(r["findings"]))]
    hard = [r for r in brk if any(x["status"] == "BREAK" and x["continueOnError"] is not True for x in r["findings"])]
    ref = [r for r in brk if any(x["status"] == "BREAK" and "26.04 image" in x["where"] for x in r["findings"])]
    otp = [r for r in brk if any(x["status"] == "BREAK" and "26.04->None" in x["where"] for x in r["findings"])]
    lo, hi = wilson(len(brk), len(exp))
    return {"repos": len(rows), "exposed": len(exp), "break": len(brk),
            "share": f"{100 * len(brk) / max(1, len(exp)):.1f}%", "wilson95": f"{100 * lo:.1f}-{100 * hi:.1f}%",
            "newlyRed": sum(newly_red(r["findings"]) for r in brk), "breakNotContinueOnError": len(hard),
            "breakByOtp": len(otp), "breakByRef": len(ref), "breakOrUnknown": len(brk) + len(unk)}


def main():
    rows = [json.loads(line) for line in open(sys.argv[1])]
    out = {"all": cut(rows)}
    if len(sys.argv) > 2:
        heads = dict(line.split() for line in open(sys.argv[2]) if len(line.split()) == 2)
        as_of = datetime.date.fromisoformat(sys.argv[3]) if len(sys.argv) > 3 else datetime.date.today()
        for days in (365, 90):
            def recent(r):
                d = heads.get(os.path.basename(os.path.normpath(r["repo"])))
                return d is not None and (as_of - datetime.date.fromisoformat(d)).days <= days
            out[f"commitWithin{days}d"] = cut([r for r in rows if recent(r)])
    for name, c in out.items():
        print(f"{name:18}", " ".join(f"{k}={v}" for k, v in c.items()))
    statuses = collections.Counter(x["status"] for r in rows for x in beam(r["findings"]))
    specs = collections.Counter(x["spec"] for r in rows for x in r["findings"] if x["status"] == "BREAK")
    print("setup-beam entries by status:", dict(statuses))
    print("BREAK entries by otp-version:", dict(specs.most_common()))


if __name__ == "__main__":
    main()
