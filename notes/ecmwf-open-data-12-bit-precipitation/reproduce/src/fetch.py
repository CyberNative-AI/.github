"""Fetch tp (and lsm) GRIB messages from the ECMWF open-data Google mirror by byte range.
Usage: fetch.py OUTDIR DATE STREAM STEPS(comma) [--lsm]
Writes OUTDIR/DATE/STREAM/<step>.grib2 (concatenated tp messages, index order) and <step>.index.json; skips existing."""
import json, sys, time, urllib.request, urllib.error, pathlib, hashlib
G = "https://storage.googleapis.com/ecmwf-open-data/"
def get(url, rng=None):
    h = {"Range": f"bytes={rng[0]}-{rng[1]}"} if rng else {}
    for k in range(8):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=120).read()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            time.sleep(2 * (k + 1))
    raise SystemExit(f"failed {url}")
out, date, stream, steps = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3], [int(s) for s in sys.argv[4].split(",")]
params = {"tp"} | ({"lsm"} if "--lsm" in sys.argv else set())
typ = {"oper": "fc", "enfo": "ef"}[stream]
d = out / date / stream; d.mkdir(parents=True, exist_ok=True)
for st in steps:
    f = d / f"{st}.grib2"
    if f.exists(): continue
    stem = f"{date}/00z/ifs/0p25/{stream}/{date}000000-{st}h-{stream}-{typ}"
    idx = [json.loads(l) for l in get(G + stem + ".index").decode().splitlines() if l.strip()]
    sel = [x for x in idx if x.get("param") in params]
    buf = b"".join(get(G + stem + ".grib2", (x["_offset"], x["_offset"] + x["_length"] - 1)) for x in sel)
    (d / f"{st}.index.json").write_text(json.dumps(sel))
    tmp = f.with_suffix(".part"); tmp.write_bytes(buf); tmp.rename(f)
    print(date, stream, st, len(sel), len(buf), hashlib.sha256(buf).hexdigest()[:16], flush=True)
    time.sleep(0.3)
