"""Judge and checker controls. Runs inside the sandbox after `judge.py prep`.
  python3 -I /src/controls.py /out/tests > /out/controls.json ; exit 0 only if every control holds.
"""
import json
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checkers import CHECKERS, check  # noqa: E402
from judge import judge_record  # noqa: E402

res = {}


def expect(name, cond):
    res[name] = bool(cond)


testdir = Path(sys.argv[1])

# 1. Checkers accept every stored reference output, and reject mutations.
for qid in sorted(CHECKERS):
    p = json.loads((testdir / f"{qid}.json").read_text())
    ok = rej = n_mut = 0
    for inp, exp in zip(p["inputs"], p["outputs"]):
        ok += check(qid, inp, exp, exp)
        e = exp.split()
        muts = []
        if qid == "abc385_f" and e != ["-1"]:
            b = Decimal(e[0])
            scale = max(Decimal(1), abs(b))
            muts = [str(b + Decimal("3e-9") * scale), str(b + Decimal("1e-7") * scale), "-1"]
            expect(f"{qid}:half-tolerance-accepted:{len(res)}", check(qid, inp, exp, str(b + Decimal("0.5e-9") * scale)))
        elif qid == "abc396_e" and e != ["-1"]:
            a = [int(x) for x in e]
            a[0] ^= 1
            muts = [" ".join(map(str, a)), "-1"]
        elif qid == "arc190_a" and e != ["-1"]:
            muts = [" ".join([str(int(e[0]) + 1)] + e[1:]), "-1"]
            # keep K consistent but break coverage: turn one active op into a different active op
            ops = e[1:]
            for j, o in enumerate(ops):
                if o in ("1", "2"):
                    alt = ops[:j] + ["2" if o == "1" else "1"] + ops[j + 1:]
                    t = inp.split()
                    n_, l_, r_ = int(t[0]), int(t[2 + 2 * j]), int(t[3 + 2 * j])
                    if not (l_ == 1 and r_ == n_):  # flipping a full-range op can still cover
                        muts.append(" ".join([e[0]] + alt))
                    break
        elif qid == "arc195_c":
            muts = [exp.replace("Yes", "Q", 1).replace("No", "Yes", 1).replace("Q", "No", 1)] if ("Yes" in e and "No" in e) else []
            # move the first piece's row by 5 (breaks adjacency, stays in bounds and distinct)
            if "Yes" in e:
                i = e.index("Yes")
                if i + 3 < len(e) and e[i + 1] in ("R", "B"):
                    m2 = e[:]
                    m2[i + 2] = str(int(m2[i + 2]) + 5)
                    muts.append(" ".join(m2))
        elif e == ["-1"]:
            muts = ["0"]
        for m in muts:
            n_mut += 1
            rej += not check(qid, inp, exp, m)
    expect(f"{qid}:reference-accepted {ok}/{len(p['inputs'])}", ok == len(p["inputs"]))
    expect(f"{qid}:mutations-rejected {rej}/{n_mut}", rej == n_mut and n_mut > 0)

# 2. Judge mechanics on synthetic problems.
SUM = {"qid": "synthetic_sum", "testtype": "stdin", "fn_name": None,
       "inputs": ["3\n1 2 3\n", "2\n10 -4\n"], "outputs": ["6", "6"]}
progs = {
    "buffer_readline_PASS": "import sys\nn=int(sys.stdin.buffer.readline())\nprint(sum(map(int,sys.stdin.buffer.readline().split())))",
    "input_PASS": "n=int(input())\nprint(sum(map(int,input().split())))",
    "uses_import_header_PASS": "d=deque(map(int,open(0).read().split()[1:]))\nprint(sum(d))",
    "wrong_WA": "print(7)",
    "extra_line_WA": "n=int(input())\nprint(sum(map(int,input().split())))\nprint()\nprint(1)",
    "loop_TLE": "while True: pass",
    "sysexit_noprint_WA": "raise SystemExit(3)",
    "raise_RE": "raise ValueError(3)",
    "empty_NOCODE": "   ",
    "exit_after_print_PASS": "import sys\nn=int(input())\nprint(sum(map(int,input().split())))\nsys.exit(1)",
    "main_guard_PASS": "def main():\n    n=int(input())\n    print(sum(map(int,input().split())))\nif __name__ == '__main__':\n    main()",
    "numpy_PASS": "import numpy as np\nn=int(input())\nprint(int(np.array(input().split(),dtype=np.int64).sum()))",
    "scipy_PASS": "import scipy.sparse, sys\nn=int(input())\nprint(sum(map(int,input().split())))",
    "crash_after_print_RE": "n=int(input())\nprint(sum(map(int,input().split())))\nraise ValueError('x')",
}
for name, code in progs.items():
    v = judge_record({"code": code}, SUM, 2.0)["verdict"]
    expect(f"stdin:{name}->{v}", v == name.rsplit("_", 1)[1])
FN = {"qid": "synthetic_fn", "testtype": "functional", "fn_name": "f",
      "inputs": ["[1, 2]\n3", "[]\n0"], "outputs": ["[1, 2, 3]", "[0]"]}
fprogs = {
    "tuple_PASS": "class Solution:\n    def f(self, a: List[int], x: int):\n        print('noise')\n        return tuple(a + [x])",
    "wrong_WA": "class Solution:\n    def f(self, a, x):\n        return a",
    "fake_nonce_WA": "class Solution:\n    def f(self, a, x):\n        print('@@deadbeef@@1')\n        return []",
}
NEST = {"qid": "synthetic_nest", "testtype": "functional", "fn_name": "f", "inputs": ["1"], "outputs": ["[[1, 2]]"]}
expect("functional:nested_tuple_WA (stock semantics)",
       judge_record({"code": "class Solution:\n    def f(self, x):\n        return [(1, 2)]"}, NEST, 2.0)["verdict"] == "WA")
expect("functional:nested_list_PASS",
       judge_record({"code": "class Solution:\n    def f(self, x):\n        return [[1, 2]]"}, NEST, 2.0)["verdict"] == "PASS")
for name, code in fprogs.items():
    v = judge_record({"code": code}, FN, 2.0)["verdict"]
    expect(f"functional:{name}->{v}", v == name.rsplit("_", 1)[1])
FLOAT = {"qid": "synthetic_float", "testtype": "stdin", "fn_name": None, "inputs": [""], "outputs": ["1.50"]}
expect("stdin:decimal_equal_PASS", judge_record({"code": "print('1.5')"}, FLOAT, 2.0)["verdict"] == "PASS")

json.dump(res, sys.stdout, indent=1, sort_keys=True)
print()
bad = [k for k, v in res.items() if not v]
print("FAILED:", bad, file=sys.stderr) if bad else print("all controls hold", file=sys.stderr)
sys.exit(1 if bad else 0)
