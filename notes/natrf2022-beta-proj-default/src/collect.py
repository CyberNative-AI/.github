"""A0: NGS NCAT beta reference outputs. Resumable JSONL; >=2.5 s between points; raw HTML hashed."""
import json, sys, time, hashlib, random, urllib.error
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ncat
HERE = Path(__file__).resolve().parent.parent
def main(tag="a0"):
    pts = json.loads((HERE / "data" / "frame.json").read_text())
    if tag == "repeat":  # C1: 10 seeded points re-queried after the main pass
        pts = random.Random(134620).sample(pts, 10)
    out = HERE / "out" / f"ncat_{tag}.jsonl"
    done = set()
    if out.exists():
        done = {json.loads(l)["id"] for l in out.read_text().splitlines() if l.strip()}
    consecutive_err = 0
    with out.open("a", encoding="utf-8") as f:
        for p in pts:
            if p["id"] in done:
                continue
            rec = {"id": p["id"], "lat": p["lat"], "lon": p["lon"], "t": datetime.now(timezone.utc).isoformat()}
            for attempt in range(3):
                try:
                    d, raw = ncat.convert(p["lat"], p["lon"])
                    rec.update(d); rec["raw_sha256"] = hashlib.sha256(raw.encode()).hexdigest(); rec["raw_len"] = len(raw)
                    echo_ok = d.get("in_lat") is not None and abs(d["in_lat"] - p["lat"]) < 1e-9 and abs(d["in_lon"] - p["lon"]) < 1e-9
                    rec["echo_ok"] = echo_ok
                    if d.get("parse_ok") and d.get("out_lat") is not None and echo_ok:
                        rec["status"] = "VALID"
                    elif d.get("parse_ok") and d.get("explicit_na"):
                        rec["status"] = "NA"
                    else:
                        rec["status"] = "ERROR"; rec["error"] = "parse/echo failure"
                        (HERE / "out" / "raw_errors").mkdir(exist_ok=True)
                        (HERE / "out" / "raw_errors" / f"{p['id']}.html").write_text(raw, encoding="utf-8")
                    break
                except urllib.error.HTTPError as e:
                    rec["status"] = "ERROR"; rec["error"] = f"HTTP {e.code}"
                    if e.code in (403, 429):
                        f.write(json.dumps(rec, sort_keys=True) + "\n"); f.flush()
                        sys.exit(f"ABORT: HTTP {e.code} at {p['id']}")
                    time.sleep(10)
                except Exception as e:  # recorded, retried twice with backoff
                    rec["status"] = "ERROR"; rec["error"] = f"{type(e).__name__}: {e}"[:300]
                    time.sleep(10)
            f.write(json.dumps(rec, sort_keys=True) + "\n"); f.flush()
            print(rec["id"], rec["status"], rec.get("out_lat"), rec.get("out_lon"), flush=True)
            consecutive_err = consecutive_err + 1 if rec["status"] == "ERROR" else 0
            if consecutive_err >= 5:
                sys.exit(f"ABORT: 5 consecutive ERRORs at {p['id']}")
            time.sleep(2.5)
if __name__ == "__main__":
    main(*(sys.argv[1:] or []))
