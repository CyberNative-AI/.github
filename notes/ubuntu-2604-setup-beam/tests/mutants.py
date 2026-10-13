"""Seed faults into checkbeam2604.py and check that the tests or the parity check catch each one.

usage: python3 tests/mutants.py
Each mutant is one source replacement in a scratch copy of this directory; it is caught when
`python3 -m unittest discover -s tests` or `python3 tests/parity/compare.py` fails.
"""
import os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MUTANTS = [
    ("old ref passes", 'if "ubuntu26" not in images:\n        causes', 'if False:\n        causes'),
    ("24.04 failure not ALREADY", 'if r24 is None or r24.startswith("ERROR"):', "if False:"),
    ("ref without 24.04 support", 'if "ubuntu24" not in images:', "if False:"),
    ("version-file without strict accepted", "if not strict:\n            return", "if False:\n            return"),
    (".tool-versions first line wins", "found = m.group(3)", "found = found or m.group(3)"),
    ("include extends added entries", "combos.append(dict(e))", "combos.append(dict(e))\n            originals.append(dict(e))"),
    ("any ubuntu label counts", 'return runs_on.strip() == "ubuntu-latest"', 'return runs_on.strip().startswith("ubuntu")'),
    ("container jobs checked", 'if job.get("container"):', "if False:"),
    ("ImageOS override ignored", 'if "ImageOS" in sctx["env"]:', "if False:"),
    ("RC spec matched as a range", "if strict or is_rc(spec0) or _branchy(spec0)", "if strict or _branchy(spec0)"),
    ("4th version part ignored", "if that and _range(that).intersects(_range(this_range)):", "if that:"),
    ("tilde too wide", 'return f">={M}.{mi}.0 <{M}.{int(mi) + 1}.0-0"\n    if pr:', 'return f">={M}.{mi}.0 <{int(M) + 1}.0.0-0"\n    if pr:'),
    ("short SHA not placed", "if len(hits) == 1:", "if len(hits) == 2:"),
    ("YAML float kept as written", "return str(int(v)) if v.is_integer() else repr(v)", "return repr(v)"),
    ("OTP- prefix kept", 'return v[4:] if v.startswith("OTP-") else v', "return v"),
    ("continue-on-error lost", "soft = soft_job is True or (", "soft = False and ("),
]


def run(d):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    t = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=d, env=env, capture_output=True)
    p = subprocess.run([sys.executable, "tests/parity/compare.py"], cwd=d, env=env, capture_output=True)
    return t.returncode, p.returncode


def main():
    tmp = tempfile.mkdtemp()
    try:
        d = os.path.join(tmp, "note")
        shutil.copytree(ROOT, d, ignore=shutil.ignore_patterns("__pycache__", "data"))
        shutil.copytree(os.path.join(HERE, "data"), os.path.join(d, "tests", "data"))
        src = os.path.join(d, "checkbeam2604.py")
        with open(src) as f:
            orig = f.read()
        assert run(d) == (0, 0), "unmutated tests must pass"
        caught = 0
        for name, a, b in MUTANTS:
            assert orig.count(a) == 1, f"mutant {name!r} does not match exactly once"
            with open(src, "w") as f:
                f.write(orig.replace(a, b))
            t, p = run(d)
            ok = t != 0 or p != 0
            caught += ok
            print(f"{'caught' if ok else 'MISSED'}  tests={'fail' if t else 'pass'} parity={'fail' if p else 'pass'}  {name}")
        print(f"{caught} of {len(MUTANTS)} mutants caught")
        return 0 if caught == len(MUTANTS) else 1
    finally:
        shutil.rmtree(tmp)


if __name__ == "__main__":
    sys.exit(main())
