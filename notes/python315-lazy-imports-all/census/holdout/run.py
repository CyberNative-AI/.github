"""Run walk.py per unit x arm x repeat. Inside container, --network none.

Usage: python run.py UNITS.json OUTDIR WORKERS
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ARMS = tuple(os.environ.get("ARMS", "normal,all").split(","))
REPS = (1, 2)
TIMEOUT = 90


def job(u, arm, rep, outdir):
    out = outdir / f"{u['project']}__{arm}__{rep}.json"
    if out.exists():
        return
    py = u.get("python") or f"/w/envs/{u['project']}/bin/python"
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp", "PYTHONHASHSEED": "0",
           "PYTHONDONTWRITEBYTECODE": "1", "MPLBACKEND": "Agg", "NO_COLOR": "1"}
    if u.get("pythonpath"):
        env["PYTHONPATH"] = u["pythonpath"]
    if arm == "deny":
        env["LAZY_DENY"] = ",".join(u["deny"])
    if arm == "eco":  # amendment 01: ecosystem denylist filter
        env["LAZY_DENY_FILE"] = "/src/denylist.json"
    xmode = "all" if arm in ("deny", "eco") else arm
    cmd = [py, "-X", f"lazy_imports={xmode}", "-W", "ignore", "/src/walk.py", *u["names"]]
    rec = {"project": u["project"], "arm": arm, "rep": rep, "cmd": cmd}
    try:
        cp = subprocess.run(cmd, cwd="/tmp/empty", env=env, capture_output=True, text=True,
                            timeout=TIMEOUT, errors="replace")
        rec["rc"] = cp.returncode
        rec["stderr_tail"] = cp.stderr[-2000:]
        line = cp.stdout.strip().splitlines()[-1] if cp.stdout.strip() else ""
        try:
            rec["result"] = json.loads(line) if line else None
        except json.JSONDecodeError:
            rec["result"] = None
            rec["stdout_tail"] = cp.stdout[-2000:]
    except subprocess.TimeoutExpired as e:
        rec["rc"] = "TIMEOUT"
        rec["result"] = None
        rec["stderr_tail"] = (e.stderr or b"")[-2000:].decode("utf-8", "replace") if isinstance(e.stderr, bytes) else str(e.stderr)[-2000:]
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec, sort_keys=True) + "\n", encoding="utf-8")
    tmp.rename(out)


def main():
    units = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    outdir = Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    os.makedirs("/tmp/empty", exist_ok=True)
    jobs = [(u, a, r) for u in units if u.get("names") for a in ARMS for r in REPS]
    with ThreadPoolExecutor(int(sys.argv[3])) as ex:
        list(ex.map(lambda t: job(*t, outdir), jobs))


main()
