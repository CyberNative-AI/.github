"""Driver: run worker.py over an input TSV in chunks, in parallel, resumable.

usage: python drive.py PYTHON MODE IN_TSV OUT_DIR [--jobs N] [--chunk N] [--timeout S]
A chunk whose worker exceeds the timeout is bisected down to single molecules; a single
molecule that still exceeds it is written as {"id":..., "err":"TIMEOUT"}.
Finished chunks are OUT_DIR/c<start>-<end>.jsonl (+ .meta); existing ones are skipped.
"""
import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

WORKER = str(Path(__file__).with_name("worker.py"))


def run(py, mode, rows, out, timeout, tmp):
    name = out / f"c{rows[0][0]}-{rows[-1][0]}.jsonl"
    if name.exists():
        return
    inp = tmp / (name.stem + ".in")
    inp.write_text("".join(r[1] for r in rows), encoding="utf-8")
    part = tmp / (name.stem + ".part")
    try:
        subprocess.run([py, "-I", WORKER, mode, str(inp), str(part)], timeout=timeout, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        os.replace(str(part) + ".meta", str(name) + ".meta")
        os.replace(part, name)
    except subprocess.TimeoutExpired:
        if len(rows) == 1:
            cid = rows[0][1].split("\t")[0]
            name.write_text(json.dumps({"id": cid, "err": "TIMEOUT", "ms": timeout * 1000}) + "\n")
        else:
            h = len(rows) // 2
            run(py, mode, rows[:h], out, timeout, tmp)
            run(py, mode, rows[h:], out, timeout, tmp)
    finally:
        inp.unlink(missing_ok=True)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("python"); a.add_argument("mode"); a.add_argument("inp"); a.add_argument("out")
    a.add_argument("--jobs", type=int, default=4); a.add_argument("--chunk", type=int, default=5000)
    a.add_argument("--timeout", type=int, default=900)
    g = a.parse_args()
    out = Path(g.out); out.mkdir(parents=True, exist_ok=True)
    tmp = out / "_tmp"; tmp.mkdir(exist_ok=True)
    lines = Path(g.inp).read_text(encoding="utf-8").splitlines(keepends=True)
    rows = list(enumerate(lines))
    chunks = [rows[i:i + g.chunk] for i in range(0, len(rows), g.chunk)]
    with ThreadPoolExecutor(g.jobs) as ex:
        list(ex.map(lambda c: run(g.python, g.mode, c, out, g.timeout, tmp), chunks))
    n = sum(1 for p in out.glob("c*.jsonl") for _ in open(p, encoding="utf-8"))
    print(json.dumps({"rows_in": len(rows), "rows_out": n}), file=sys.stderr)
    sys.exit(0 if n == len(rows) else 3)


if __name__ == "__main__":
    main()
