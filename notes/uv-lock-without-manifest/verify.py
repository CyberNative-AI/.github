"""Compare uv tree on a generated lockfile with and without its manifest."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from make_fixture import main as make_fixture


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", required=True, type=Path)
    parser.add_argument("--new", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    binaries = {"0.12.22": args.old.resolve(), "0.12.23": args.new.resolve()}
    for version, binary in binaries.items():
        observed = subprocess.run([binary, "--version"], check=True, capture_output=True, text=True).stdout
        assert observed.startswith("uv " + version + " "), observed
    previous_argv = sys.argv
    sys.argv = ["make_fixture.py", str(root / "project")]
    make_fixture()
    sys.argv = previous_argv
    rows = []

    def run(label, version, commands, directory, expected):
        command = [str(binaries[version]), *commands, "--offline", "--no-cache", "--no-python-downloads", "--python", sys.executable]
        r = subprocess.run(command, cwd=root / directory, capture_output=True, text=True, timeout=30)
        stdout = r.stdout.replace(str(root), "<fixture>")
        stderr = r.stderr.replace(str(root), "<fixture>").replace(sys.executable, "python3")
        row = {"label": label, "version": version, "directory": directory,
               "args": command[1:-1] + ["python3"], "exit": r.returncode,
               "expectedExit": expected, "stdout": stdout, "stderr": stderr}
        rows.append(row)
        (root / "command-receipts.json").write_text(json.dumps(rows, indent=2) + "\n")
        assert r.returncode == expected, row
        return row

    run("generate-lock", "0.12.23", ["lock", "--no-index", "--find-links", "."], "project", 0)
    (root / "standalone").mkdir()
    (root / "empty").mkdir()
    shutil.copyfile(root / "project/uv.lock", root / "standalone/uv.lock")
    lock_before = (root / "standalone/uv.lock").read_bytes()
    complete = run("old-manifest-control", "0.12.22", ["tree", "--frozen"], "project", 0)
    run("old-standalone", "0.12.22", ["tree", "--frozen"], "standalone", 2)
    warning = run("new-standalone-warning", "0.12.23", ["tree", "--frozen"], "standalone", 0)
    explicit = run("new-standalone-explicit-preview", "0.12.23", ["tree", "--frozen", "--preview-features", "frozen-lockfile"], "standalone", 0)
    run("new-unfrozen-control", "0.12.23", ["tree"], "standalone", 2)
    run("new-no-lock-control", "0.12.23", ["tree", "--frozen"], "empty", 2)
    export = run("new-export", "0.12.23", ["export", "--frozen", "--preview-features", "frozen-lockfile", "--no-hashes"], "standalone", 0)
    assert warning["stdout"] == explicit["stdout"] == complete["stdout"]
    assert "demo-parent v1.0.0" in explicit["stdout"] and "demo-leaf v1.0.0" in explicit["stdout"]
    assert "preview" in warning["stderr"] and "preview" not in explicit["stderr"]
    assert "demo-parent==1.0.0" in export["stdout"]
    assert "demo-leaf==1.0.0" in export["stdout"]
    assert (root / "standalone/uv.lock").read_bytes() == lock_before
    assert sorted(p.name for p in (root / "standalone").iterdir()) == ["uv.lock"]
    assert not list(root.rglob(".venv"))
    report = {"checkedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "python": sys.version.split()[0], "platform": sys.platform,
              "lockSha256": hashlib.sha256(lock_before).hexdigest(),
              "lockUnchanged": True, "standaloneFiles": ["uv.lock"],
              "installedEnvironmentCreated": False, "rows": rows}
    (root / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
