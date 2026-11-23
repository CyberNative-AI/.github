"""Run the fixture suite on the original checker, then on each seeded fault."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

TOOL = Path(__file__).resolve().parents[1]
SUITE = [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests"]

MUTANTS = {
    "cache-2604-equals-2404": ('hits = [v for v in data.cache[osv]["python"]', 'hits = [v for v in data.cache["24.04"]["python"]'),
    "ignore-platform-version": ('f.get("platform_version") == osv', 'True'),
    "no-exclude": ('combos = [c for c in combos if not any(', 'combos = [c for c in combos if True or not any('),
    "unknown-expr-defaults": ('    if not m or m.group(1) not in ctx:\n        raise Unknown(f"expression ${{{{ {e} }}}}")',
                              '    if not m or m.group(1) not in ctx:\n        return "3.12"'),
    "case-sensitive-keys": ('same = gh_same_text(k, name) if isinstance(k, str) else False', 'same = k == name'),
    "no-symlink-guard": ('    if os.path.commonpath([base, p]) != base:\n        return None\n', ''),
    "float-as-python-str": ('return str(int(v)) if v.is_integer() else repr(v)', 'return "%.2f" % v'),
    "ruby-ignore-asset": ('return engine, ver, data.ruby_asset(engine, ver, osv)', 'return engine, ver, 200'),
    "runs-on-any-ubuntu": ('return _ubuntu_latest(runs_on)', 'return runs_on.strip().lower().startswith("ubuntu")'),
    "case-sensitive-compare": ('if ka == kb == "str":\n        same = gh_same_text(a, b)',
                               'if ka == kb == "str":\n        same = a == b'),
    "no-explicit-ruby-file": ('elif raw in (".ruby-version", ".tool-versions", "mise.toml"):', 'elif False:'),
    "fallback-unknown-is-null": ('            v = gh_value(p, ctx) if p.startswith("matrix") else lookup(p, ctx)',
                                 '            if p.startswith("matrix"):\n'
                                 '                v = gh_value(p, ctx)\n'
                                 '            else:\n'
                                 '                try:\n'
                                 '                    v = lookup(p, ctx)\n'
                                 '                except Unknown:\n'
                                 '                    v = None'),
    "fallback-missing-key-unknown": ('            v = None if v is _MISSING else v',
                                     '            if v is _MISSING:\n'
                                     '                raise Unknown(f"missing key in {e.strip()}")'),
    "include-extends-added": ('            combos.append(dict(e))\n', '            combos.append(dict(e))\n            originals.append(dict(e))\n'),
    "soft-unknown-kills-job": ('                    soft = None  # continue-on-error', '                    raise  # continue-on-error'),
    "no-local-action-follow": ('    return uses[2:].rstrip("/") or "."', '    return None'),
    "no-action-yaml": ('    for name in ("action.yml", "action.yaml"):', '    for name in ("action.yml",):'),
    "one-level-of-local-actions": ('    if depth >= MAX_ACTION_DEPTH:', '    if depth >= 1:'),
    "read-manifest-after-run": ('    if why:\n        raise Unknown(f"local action {label} {why}")',
                                '    if why and why != "may be changed by an earlier step (a run step)":\n'
                                '        raise Unknown(f"local action {label} {why}")'),
}


def run_suite(tree):
    return subprocess.run(SUITE, cwd=tree, capture_output=True, text=True)


def main():
    baseline = run_suite(TOOL)
    if baseline.returncode != 0:
        raise SystemExit("Baseline suite failed; no mutants ran.")
    print(f"Baseline passed: {baseline.stderr.strip().splitlines()[-1]}", flush=True)

    source = (TOOL / "check2604.py").read_text(encoding="utf-8")
    for name, (before, _) in MUTANTS.items():
        if source.count(before) != 1:
            raise SystemExit(f"{name}: expected exactly one source match.")

    caught_count = 0
    for name, (before, after) in MUTANTS.items():
        with tempfile.TemporaryDirectory() as directory:
            tree = Path(directory) / "note"
            shutil.copytree(TOOL, tree, ignore=shutil.ignore_patterns("__pycache__"))
            changed = source.replace(before, after, 1)
            compile(changed, "check2604.py", "exec")
            (tree / "check2604.py").write_text(changed, encoding="utf-8")
            result = run_suite(tree)
        caught = result.returncode == 1 and "\nFAIL: " in result.stderr
        caught_count += caught
        verdict = "caught" if caught else "SURVIVED" if result.returncode == 0 else "suite error"
        detail = result.stderr.strip().splitlines()
        print(f"{name:26} {verdict}  {detail[-1] if detail else 'no test output'}", flush=True)
        if verdict == "suite error":
            print(result.stderr, file=sys.stderr)

    print(f"{caught_count}/{len(MUTANTS)} mutants caught")
    return caught_count != len(MUTANTS)


if __name__ == "__main__":
    sys.exit(main())
