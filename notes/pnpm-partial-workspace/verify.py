#!/usr/bin/env python3
"""Reproduce one pnpm frozen-install boundary with dependency-free inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", type=Path, required=True, help="absolute pnpm 11.28.3 path")
    parser.add_argument("--new", type=Path, required=True, help="absolute pnpm 11.28.4 path")
    parser.add_argument("--output", type=Path, required=True, help="new output directory")
    args = parser.parse_args()
    binaries = [("11.28.3", args.old), ("11.28.4", args.new)]
    for version, binary in binaries:
        if not binary.is_absolute() or not binary.is_file():
            parser.error(f"{version}: give an absolute existing executable path")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    config = output / "empty.npmrc"
    config.write_text("")
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "CI": "true",
        "XDG_CONFIG_HOME": str(output / "config"),
        "XDG_DATA_HOME": str(output / "data"),
        "XDG_CACHE_HOME": str(output / "cache"),
        "PNPM_HOME": str(output / "pnpm-home"),
        "NPM_CONFIG_USERCONFIG": str(config),
        "NPM_CONFIG_GLOBALCONFIG": str(config),
    }
    for version, binary in binaries:
        result = subprocess.run([str(binary), "--version"], env=env,
                                capture_output=True, text=True, timeout=20)
        if result.returncode or result.stdout.strip() != version:
            parser.error(f"expected pnpm {version}; executable version did not match")
    fixture = Path(__file__).resolve().parent / "fixture"
    rows = []
    for version, binary in binaries:
        for condition in ("complete", "absent-directory", "present-no-manifest", "changed-manifest"):
            work = output / (version + "-" + condition)
            shutil.copytree(fixture, work)
            if condition == "absent-directory":
                shutil.rmtree(work / "tests")
            elif condition == "present-no-manifest":
                (work / "tests" / "package.json").unlink()
            elif condition == "changed-manifest":
                manifest = work / "server" / "package.json"
                data = json.loads(manifest.read_text())
                data["dependencies"] = {"no-package-is-fetched": "1.0.0"}
                manifest.write_text(json.dumps(data) + "\n")
            lock = work / "pnpm-lock.yaml"
            before = sha(lock)
            command = [str(binary), "install", "--offline", "--frozen-lockfile",
                       "--ignore-scripts", "--store-dir", str(output / "store")]
            result = subprocess.run(command, env=env, cwd=work,
                                    capture_output=True, text=True, timeout=30)
            log = result.stdout + result.stderr
            # Local logs retain the full process output. Recorded JSON has no private paths.
            (work / "command.log").write_text(log)
            expected = 0 if condition == "complete" or (
                condition == "absent-directory" and version == "11.28.4") else 1
            outdated = "ERR_PNPM_OUTDATED_LOCKFILE" in log
            row = {"version": version, "condition": condition,
                   "exit": result.returncode, "expected_exit": expected,
                   "outdated_lockfile": outdated, "lock_sha256": sha(lock),
                   "lock_unchanged": before == sha(lock),
                   "lock_diff_matches_expected": lock.read_bytes() == (
                       (fixture / "pnpm-lock.yaml").read_bytes().replace(b"\n  tests: {}\n", b"")
                       if condition == "absent-directory" and version == "11.28.4"
                       else (fixture / "pnpm-lock.yaml").read_bytes()),
                   "tests_importer_present": "  tests: {}" in lock.read_text(),
                   "tests_directory_exists": (work / "tests").exists()}
            expected_unchanged = not (condition == "absent-directory" and version == "11.28.4")
            row["pass"] = result.returncode == expected and row["lock_diff_matches_expected"] and (row["lock_unchanged"] == expected_unchanged) and (
                expected == 0 or outdated)
            if condition == "absent-directory":
                row["pass"] = row["pass"] and not row["tests_directory_exists"]
                row["pass"] = row["pass"] and (row["tests_importer_present"] == (version == "11.28.3"))
            if condition == "present-no-manifest" and version == "11.28.4":
                row["pass"] = row["pass"] and "directory has no package.json" in log
            rows.append(row)
            print(f"pnpm {version}: {condition}: exit {result.returncode}; "
                  f"lock unchanged={row['lock_unchanged']}; {'PASS' if row['pass'] else 'FAIL'}")
    (output / "results.json").write_text(json.dumps(rows, indent=2) + "\n")
    return 0 if all(row["pass"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
