"""Compare two pinned Ruff policies on small, original Python examples."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True, help="Path to the Ruff 0.15.0 binary")
    parser.add_argument("--after", required=True, help="Path to the Ruff 0.16.0 binary")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    rows = []
    for path, expected in [(args.before, "ruff 0.15.0"), (args.after, "ruff 0.16.0")]:
        actual = subprocess.check_output([path, "--version"], text=True).strip()
        if actual != expected:
            raise SystemExit(f"Expected {expected}; got {actual}")
    cases = [
        (args.before, "0.15.0", "defaults", [], "mutable_default.py", []),
        (args.before, "0.15.0", "defaults", [], "lambda_alias.py", ["E731"]),
        (args.after, "0.16.0", "defaults", [], "mutable_default.py", ["B006"]),
        (args.after, "0.16.0", "defaults", [], "lambda_alias.py", []),
        (args.after, "0.16.0", "add E731", ["--extend-select", "E731"], "mutable_default.py", ["B006"]),
        (args.after, "0.16.0", "add E731", ["--extend-select", "E731"], "lambda_alias.py", ["E731"]),
        (args.after, "0.16.0", "old selection", ["--select", "E4,E7,E9,F"], "mutable_default.py", []),
        (args.after, "0.16.0", "old selection", ["--select", "E4,E7,E9,F"], "lambda_alias.py", ["E731"]),
        (args.after, "0.16.0", "defaults", [], "mutable_default_fixed.py", []),
    ]
    for binary, version, selection, options, filename, expected_codes in cases:
        cmd = [binary, "check", "--isolated", "--no-cache", "--output-format", "json", *options, str(root / filename)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode not in (0, 1):
            raise SystemExit(result.stderr)
        codes = sorted(item["code"] for item in json.loads(result.stdout))
        if codes != expected_codes or result.returncode != bool(codes):
            raise SystemExit(f"Unexpected {version} {selection} {filename}: {codes}, exit {result.returncode}")
        rows.append({"version": version, "selection": selection, "file": filename,
                     "codes": codes, "exitCode": result.returncode})
    python_runs = {}
    for filename, expected in [
        ("mutable_default.py", "['first', 'second'] ['first', 'second'] True"),
        ("mutable_default_fixed.py", "['first'] ['second'] False"),
    ]:
        output = subprocess.check_output([sys.executable, str(root / filename)], text=True).strip()
        if output != expected:
            raise SystemExit(f"Unexpected Python result: {output}")
        python_runs[filename] = output
    print(json.dumps({"checks": rows, "python": python_runs}, indent=2))


if __name__ == "__main__":
    main()
