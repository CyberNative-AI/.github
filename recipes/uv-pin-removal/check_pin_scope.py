#!/usr/bin/env python3
"""Observe pin removal using synthetic files and isolated XDG directories.

Run with a chosen uv executable: python3 check_pin_scope.py /path/to/uv
No downloads, package installations, or real user configuration are required.
"""
import hashlib
import json
import os
import platform
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    if platform.system() != "Linux":
        raise SystemExit("This recipe supports Linux only; other platforms were not tested.")
    uv = str(Path(sys.argv[1]).resolve())
    version = subprocess.check_output([uv, "--version"], text=True).strip()
    cases = [
        ("global_plural_only", None, ".python-versions", []),
        ("global_singular_only", None, ".python-version", []),
        ("local_plural_and_global_plural", ".python-versions", ".python-versions", []),
        ("local_singular_and_global_plural", ".python-version", ".python-versions", []),
        ("explicit_global_plural", None, ".python-versions", ["--global"]),
    ]
    records = []
    # Set UV_PIN_CHECK_PARENT to a scratch directory if your environment requires it.
    with tempfile.TemporaryDirectory(prefix="uv-pin-synthetic-", dir=os.environ.get("UV_PIN_CHECK_PARENT")) as td:
        for name, local_name, global_name, extra in cases:
            root = Path(td) / name
            project = root / "project"
            project.mkdir(parents=True)
            (project / "pyproject.toml").write_text('[project]\nname = "synthetic-pin-check"\nversion = "0.0.0"\nrequires-python = ">=3.11"\n')
            config = root / "config"
            (config / "uv").mkdir(parents=True)
            empty_config = root / "empty-uv.toml"
            empty_config.write_text("")
            global_file = config / "uv" / global_name
            global_file.write_text("3.11\n3.12\n" if global_name.endswith("versions") else "3.11\n")
            local_file = project / local_name if local_name else None
            if local_file:
                local_file.write_text("3.12\n")
            original = global_file.read_bytes()
            env = {"PATH": os.environ["PATH"], "XDG_CONFIG_HOME": str(config),
                   "XDG_CACHE_HOME": str(root / "cache"), "XDG_DATA_HOME": str(root / "data"),
                   "XDG_STATE_HOME": str(root / "state")}
            cmd = [uv, "--offline", "--no-python-downloads", "--color", "never",
                   "--config-file", str(empty_config), "--directory", str(project),
                   "python", "pin", "--rm", *extra]
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=10)
            # Never publish local execution paths.
            stdout = result.stdout.replace(str(root), "<sandbox>")
            stderr = result.stderr.replace(str(root), "<sandbox>")
            records.append({"case": name, "exitCode": result.returncode,
                            "localExistsAfter": local_file.exists() if local_file else None,
                            "globalExistsAfter": global_file.exists(),
                            "globalBytesUnchanged": global_file.exists() and global_file.read_bytes() == original,
                            "stdout": stdout, "stderr": stderr})
    print(json.dumps({"version": version, "executableSha256": hashlib.sha256(Path(uv).read_bytes()).hexdigest(),
                      "platform": f"{platform.system()} {platform.machine()}", "records": records}, indent=2))


if __name__ == "__main__":
    main()
