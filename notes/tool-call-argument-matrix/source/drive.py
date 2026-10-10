"""Drive the tool-call argument matrix grid inside the container (network none).

usage: python drive.py <out_dir> <scenarios,comma> <frameworks,comma|all> <replicates>
Appends one record per cell to <out_dir>/cells.jsonl and resumes from it.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

PORT = 8765
RUN_TIMEOUT_S = 120
FRAMEWORKS = ["openai-agents", "langchain", "crewai", "smolagents", "pydantic-ai",
              "llama-index", "autogen", "strands", "google-adk"]
HERE = Path(__file__).resolve().parent


def wait_health() -> None:
    for _ in range(100):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=1)
            return
        except OSError:
            time.sleep(0.1)
    raise SystemExit("mock did not start")


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    scenarios = sys.argv[2].split(",")
    fws = FRAMEWORKS if sys.argv[3] == "all" else sys.argv[3].split(",")
    reps = int(sys.argv[4])
    cells_path = out / "cells.jsonl"
    done = set()
    if cells_path.exists():
        for line in cells_path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            done.add(r["run_id"])
    req_log = out / "requests.jsonl"
    mock = subprocess.Popen([sys.executable, str(HERE / "mock_llm.py"), str(PORT), str(req_log)])
    try:
        wait_health()
        for scen in scenarios:
            for fw in fws:
                for rep in range(1, reps + 1):
                    run_id = f"{fw}.{scen}.r{rep}"
                    if run_id in done:
                        continue
                    base = f"http://127.0.0.1:{PORT}/r/{run_id}/{scen}/v1"
                    py = f"/opt/venv-{fw}/bin/python"
                    t0 = time.time()
                    try:
                        env = dict(os.environ, RUN_ID=run_id, TOOL_LOG=str(out / "tools.jsonl"))
                        p = subprocess.run([py, str(HERE / "run_one.py"), fw, scen, base], capture_output=True,
                                           text=True, timeout=RUN_TIMEOUT_S, cwd="/tmp", env=env)
                        rc, stdout, stderr = p.returncode, p.stdout, p.stderr
                        timed_out = False
                    except subprocess.TimeoutExpired as e:
                        rc, stdout, stderr, timed_out = None, (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or ""), "", True
                    wall = round(time.time() - t0, 2)
                    result = None
                    for line in stdout.splitlines():
                        if line.startswith("RESULT "):
                            result = json.loads(line[7:])
                    rec = {"run_id": run_id, "framework": fw, "scenario": scen, "replicate": rep, "rc": rc,
                           "timed_out": timed_out, "wall_s": wall, "result": result,
                           "stderr_tail": stderr[-600:] if result is None else ""}
                    with open(cells_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(rec, sort_keys=True) + "\n")
                    print(run_id, wall, (result or {}).get("outcome"), (result or {}).get("type"), flush=True)
    finally:
        mock.terminate()


if __name__ == "__main__":
    main()
