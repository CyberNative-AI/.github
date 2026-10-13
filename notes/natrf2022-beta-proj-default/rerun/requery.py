"""Rerun (b): independent NCAT beta re-query of 30 frame points, seed 13471, >=3 s apart, compared with committed out/ncat_a0.jsonl.
Usage: python3 -I rerun/requery.py   (run from anywhere; imports the frozen src/ncat.py unmodified)"""
import json, random, sys, time, hashlib
from datetime import datetime, timezone
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src"))
import ncat
sys.path.insert(0, str(HERE / "src"))
from analyze import dist_m
frame = json.loads((HERE / "data" / "frame.json").read_text())
a0 = {r["id"]: r for r in (json.loads(l) for l in (HERE / "out" / "ncat_a0.jsonl").read_text().splitlines() if l.strip())}
pts = random.Random(13471).sample(frame, 30)
out = HERE / "rerun" / "ncat_requery.jsonl"
with out.open("w", encoding="utf-8") as f:
    errs = 0
    for p in pts:
        rec = {"id": p["id"], "lat": p["lat"], "lon": p["lon"], "stratum": p["stratum"], "t": datetime.now(timezone.utc).isoformat()}
        try:
            d, raw = ncat.convert(p["lat"], p["lon"])
            rec.update(d); rec["raw_sha256"] = hashlib.sha256(raw.encode()).hexdigest()
            echo = d.get("in_lat") is not None and abs(d["in_lat"] - p["lat"]) < 1e-9 and abs(d["in_lon"] - p["lon"]) < 1e-9
            rec["echo_ok"] = echo
            rec["status"] = "VALID" if d.get("parse_ok") and d.get("out_lat") is not None and echo else ("NA" if d.get("explicit_na") else "ERROR")
            o = a0[p["id"]]
            if rec["status"] == "VALID":
                rec["max_abs_deg_vs_a0"] = max(abs(d["out_lat"] - o["out_lat"]), abs(d["out_lon"] - o["out_lon"]))
                rec["dist_m_vs_a0"] = dist_m(o["out_lat"], o["out_lon"], d["out_lat"], d["out_lon"])[0]
                rec["spc_changed"] = (d.get("spc_zone"), d.get("spc_n"), d.get("spc_e")) != (o.get("spc_zone"), o.get("spc_n"), o.get("spc_e"))
                rec["sig_changed"] = (d.get("siglat_m"), d.get("siglon_m")) != (o.get("siglat_m"), o.get("siglon_m"))
        except Exception as e:
            rec["status"] = "ERROR"; rec["error"] = f"{type(e).__name__}: {e}"[:300]
        errs = errs + 1 if rec["status"] == "ERROR" else 0
        f.write(json.dumps(rec, sort_keys=True) + "\n"); f.flush()
        print(rec["id"], rec["status"], rec.get("max_abs_deg_vs_a0"), flush=True)
        if errs >= 3: sys.exit("ABORT: 3 consecutive ERRORs")
        time.sleep(3.2)
