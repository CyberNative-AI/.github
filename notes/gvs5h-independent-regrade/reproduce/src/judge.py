"""Independent subprocess judge for stored LCB-100 generations.

Runs INSIDE the sandbox container (network none, read-only root, non-root user).
  python3 -I /src/judge.py prep  /frame/lcb100.jsonl /out/tests
  python3 -I /src/judge.py judge /data/records.jsonl /out/tests /out/verdicts.jsonl [--workers 5] [--timeout 6] [--arms a,b]

Judge rule (fixed before judging):
  * tests = public + private in LCB order (get_evaluation_sample); stop at first non-pass.
  * every test is a fresh `python3 -I` subprocess; the code gets LCB's own import header.
  * stdin: LCB's line rule (same line count after strip; each stripped line equal, or equal as
    Decimals); the four multi-answer problems use src/checkers.py (contest rule).
  * stdin programs run as __main__ via a runner that swallows SystemExit (stock LCB does too).
  * functional: json args per input line, Solution().<fn_name>(*args), top-level tuple -> list,
    compared == json.loads(expected) inside the subprocess (stock semantics); verdict via nonce line.
  * subprocess env: single-threaded BLAS (numpy/scipy present in the image, LCB uv.lock versions).
  * per-test wall timeout --timeout s (LCB stock: 6); RLIMIT_AS 2 GiB; verdicts PASS/WA/RE/TLE/NOCODE.
Resumable: keys already in the verdicts file are skipped.
"""
import base64
import json
import os
import pickle
import resource
import secrets
import subprocess
import sys
import tempfile
import time
import zlib
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checkers import MULTI, check  # noqa: E402

# Verbatim from livecodebench lcb_runner/evaluation/testing_util.py (import_string).
IMPORT_STRING = "from string import *\nfrom re import *\nfrom datetime import *\nfrom collections import *\nfrom heapq import *\nfrom bisect import *\nfrom copy import *\nfrom math import *\nfrom random import *\nfrom statistics import *\nfrom itertools import *\nfrom functools import *\nfrom operator import *\nfrom io import *\nfrom sys import *\nfrom json import *\nfrom builtins import *\nfrom typing import *\nimport string\nimport re\nimport datetime\nimport collections\nimport heapq\nimport bisect\nimport copy\nimport math\nimport random\nimport statistics\nimport itertools\nimport functools\nimport operator\nimport io\nimport sys\nimport json\nsys.setrecursionlimit(50000)\n"

MEM = 2 * 1024 ** 3

FUNC_DRIVER = r'''
import json, sys
_NONCE = sys.argv[1]
_FN = sys.argv[2]
_src = open(sys.argv[3], encoding="utf-8").read()
_exp = json.loads(open(sys.argv[4], encoding="utf-8").read())
_args = [json.loads(l) for l in sys.stdin.read().split("\n")]
_g = {"__name__": "__solution__"}
exec(compile(_src, "solution.py", "exec"), _g)
_res = getattr(_g["Solution"](), _FN)(*_args)
if isinstance(_res, tuple):  # stock LCB: only a top-level tuple becomes a list
    _res = list(_res)
sys.stdout.write("\n" + _NONCE + ("1" if _res == _exp else "0") + "\n")
'''

# stdin runner: run the program as __main__ and swallow SystemExit, as stock LCB does in-process.
STDIN_RUNNER = r'''
import sys
_src = open(sys.argv[1], encoding="utf-8").read()
_g = {"__name__": "__main__", "__builtins__": __builtins__}
try:
    exec(compile(_src, "solution.py", "exec"), _g)
except SystemExit:
    pass
sys.stdout.flush()
'''


def prep(frame, outdir):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for ln in open(frame, encoding="utf-8"):
        d = json.loads(ln)
        pub = json.loads(d["public_test_cases"])
        try:
            priv = json.loads(d["private_test_cases"])
        except json.JSONDecodeError:
            priv = json.loads(pickle.loads(zlib.decompress(base64.b64decode(d["private_test_cases"].encode()))))
        tests = pub + priv
        meta = json.loads(d["metadata"])
        types = sorted({t["testtype"] for t in tests})
        assert len(types) == 1, (d["question_id"], types)
        rec = {"qid": d["question_id"], "platform": d["platform"], "contest_date": d["contest_date"],
               "testtype": types[0], "fn_name": meta.get("func_name"), "n_public": len(pub),
               "inputs": [t["input"] for t in tests], "outputs": [t["output"] for t in tests]}
        (out / f"{d['question_id']}.json").write_text(json.dumps(rec), encoding="utf-8")
        n += 1
    print("prepared", n, "problems")


def _limits():
    resource.setrlimit(resource.RLIMIT_AS, (MEM, MEM))
    os.setsid()


def _lines(v):
    return [x.strip() for x in v.strip().split("\n")]


def stdio_equal(got, exp):
    from decimal import Decimal, InvalidOperation
    a, b = _lines(got), _lines(exp)
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x == y:
            continue
        try:
            if [Decimal(t) for t in x.split()] != [Decimal(t) for t in y.split()]:
                return False
        except InvalidOperation:
            return False
    return True


ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin", "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1",
       "MKL_NUM_THREADS": "1", "HOME": "/tmp", "LANG": "C.UTF-8"}


def run_one(cmd, inp, timeout, cwd):
    t0 = time.monotonic()
    try:
        p = subprocess.run(cmd, input=inp.encode(), capture_output=True, timeout=timeout,
                           cwd=cwd, preexec_fn=_limits, env=ENV)
    except subprocess.TimeoutExpired:
        return "TLE", b"", time.monotonic() - t0
    dt = time.monotonic() - t0
    if p.returncode != 0:
        return "RE", p.stderr[-300:], dt
    return "OK", p.stdout, dt


def judge_record(rec, prob, timeout):
    code = rec["code"]
    if not code.strip():
        return {"verdict": "NOCODE", "n_run": 0, "max_t": 0.0}
    with tempfile.TemporaryDirectory(dir="/tmp") as td:
        sol = Path(td) / "solution.py"
        sol.write_text(IMPORT_STRING + "\n" + code if prob["testtype"] == "stdin"
                       else IMPORT_STRING + "\n\n" + code, encoding="utf-8")
        drv = Path(td) / "driver.py"
        drv.write_text(FUNC_DRIVER, encoding="utf-8")
        runner = Path(td) / "runner.py"
        runner.write_text(STDIN_RUNNER, encoding="utf-8")
        expf = Path(td) / "expected.json"
        nonce = "@@" + secrets.token_hex(8) + "@@"
        max_t = 0.0
        for i, (inp, exp) in enumerate(zip(prob["inputs"], prob["outputs"])):
            if prob["testtype"] == "stdin":
                st, out, dt = run_one([sys.executable, "-I", str(runner), str(sol)], inp, timeout, td)
            else:
                expf.write_text(exp, encoding="utf-8")
                st, out, dt = run_one([sys.executable, "-I", str(drv), nonce, prob["fn_name"], str(sol), str(expf)],
                                      inp, timeout, td)
            max_t = max(max_t, dt)
            if st != "OK":
                return {"verdict": st, "fail_test": i, "n_run": i + 1, "max_t": round(max_t, 3),
                        "detail": out.decode("utf-8", "replace")[-200:] if st == "RE" else ""}
            got = out.decode("utf-8", "replace")
            if prob["testtype"] == "stdin":
                ok = check(prob["qid"], inp, exp, got) if prob["qid"] in MULTI else stdio_equal(got, exp)
            else:
                tail = [l for l in got.split("\n") if l.startswith(nonce)]
                ok = bool(tail) and tail[-1][len(nonce):].strip() == "1"
            if not ok:
                return {"verdict": "WA", "fail_test": i, "n_run": i + 1, "max_t": round(max_t, 3)}
        return {"verdict": "PASS", "n_run": len(prob["inputs"]), "max_t": round(max_t, 3)}


def _task(args):
    qid, recs, testdir, timeout = args
    prob = json.loads((Path(testdir) / f"{qid}.json").read_text(encoding="utf-8"))
    out = []
    for r in recs:
        t0 = time.monotonic()
        try:
            v = judge_record(r, prob, timeout)
        except Exception as e:  # never let one row kill the pool
            v = {"verdict": "JUDGE_ERR", "detail": repr(e)[:200]}
        v.update({"key": r["key"], "code_sha256": r["code_sha256"], "timeout": timeout,
                  "wall": round(time.monotonic() - t0, 2)})
        out.append(v)
    return out


def judge(records, testdir, outfile, workers=5, timeout=6.0, arms=None):
    done = set()
    if Path(outfile).exists():
        done = {json.loads(l)["key"] for l in open(outfile, encoding="utf-8") if l.strip()}
    by_q = {}
    for ln in open(records, encoding="utf-8"):
        r = json.loads(ln)
        if r["key"] in done or (arms and r["arm"] not in arms):
            continue
        by_q.setdefault(r["qid"], []).append(r)
    tasks = [(q, rs, testdir, timeout) for q, rs in sorted(by_q.items())]
    print(f"{sum(len(t[1]) for t in tasks)} records in {len(tasks)} problems to judge "
          f"({len(done)} already done)", flush=True)
    with open(outfile, "a", encoding="utf-8", newline="\n") as f, Pool(workers) as pool:
        for i, res in enumerate(pool.imap_unordered(_task, tasks), 1):
            for v in res:
                f.write(json.dumps(v, sort_keys=True) + "\n")
            f.flush()
            print(f"[{time.strftime('%H:%M:%S')}] {i}/{len(tasks)} {res[0]['key'].split('|')[2]}", flush=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "prep":
        prep(a[1], a[2])
    elif a[0] == "judge":
        opts = {"workers": 5, "timeout": 6.0, "arms": None}
        rest = a[1:]
        pos = [x for x in rest if not x.startswith("--")]
        for k, v in zip(rest, rest[1:]):
            if k == "--workers":
                opts["workers"] = int(v)
            elif k == "--timeout":
                opts["timeout"] = float(v)
            elif k == "--arms":
                opts["arms"] = set(v.split(","))
        pos = [x for i, x in enumerate(rest) if not x.startswith("--") and (i == 0 or not rest[i - 1].startswith("--"))]
        judge(pos[0], pos[1], pos[2], **opts)
