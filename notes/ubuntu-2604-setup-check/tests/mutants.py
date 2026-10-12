"""Apply each mutant to a scratch copy of check2604.py and run the fixture suite; every mutant must fail it."""
import os, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); TOOL = os.path.dirname(HERE)
MUTANTS = {
    "cache-2604-equals-2404": ('"26.04": {"python": ["3.10.21", "3.11.16", "3.12.14", "3.13.15", "3.14.7"]',
                               '"26.04": {"python": ["3.10.22", "3.11.17", "3.12.15", "3.13.16", "3.14.8"]'),
    "ignore-platform-version": ('f.get("platform_version") == osv', 'True'),
    "no-exclude": ('combos = [c for c in combos if not any(', 'combos = [c for c in combos if True or not any('),
    "unknown-expr-defaults": ('    if not m:\n        raise Unknown(f"expression ${{{{ {e} }}}}")', '    if not m:\n        return "3.12"'),
    "case-sensitive-keys": ('k = next((x for x in v if', 'k = next((x for x in [] if'),
    "no-symlink-guard": ('os.path.commonpath([base, p]) != base or ', ''),
    "float-as-python-str": ('return str(int(v)) if v.is_integer() else repr(v)', 'return "%.2f" % v'),
    "ruby-ignore-asset": ('return engine, ver, data.ruby_asset(engine, ver, osv)', 'return engine, ver, 200'),
    "runs-on-any-ubuntu": ('return runs_on.strip() == "ubuntu-latest"', 'return runs_on.strip().startswith("ubuntu")'),
    "case-sensitive-compare": ('eq = left.lower() == mm.group(3).lower()', 'eq = left == mm.group(3)'),
    "no-explicit-ruby-file": ('elif raw in (".ruby-version", ".tool-versions", "mise.toml"):', 'elif False:'),
    "soft-unknown-kills-job": ('                    soft = None  # continue-on-error', '                    raise  # continue-on-error'),
}
src = open(os.path.join(TOOL, "check2604.py")).read()
bad = 0
for name, (a, b) in MUTANTS.items():
    assert src.count(a) == 1, name
    with tempfile.TemporaryDirectory() as d:
        shutil.copytree(TOOL, os.path.join(d, "t"), ignore=shutil.ignore_patterns("__pycache__"))
        open(os.path.join(d, "t", "check2604.py"), "w").write(src.replace(a, b))
        r = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests"], cwd=os.path.join(d, "t"),
                           capture_output=True, text=True)
        caught = r.returncode != 0
        bad += not caught
        print(f"{name:26} {'caught' if caught else 'SURVIVED'}  {r.stderr.strip().splitlines()[-1]}")
sys.exit(1 if bad else 0)
