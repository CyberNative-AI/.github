import os
from pathlib import Path
import subprocess
import sys

if sys.version_info[:3] != (3, 15, 0) or sys.version_info.releaselevel != "candidate" or sys.version_info.serial != 2:
    raise SystemExit("This recipe's recorded run requires CPython 3.15.0rc2.")
root = Path(__file__).resolve().parent
print(sys.version.splitlines()[0], flush=True)
env = os.environ.copy()
env.pop("PYTHON_LAZY_IMPORTS", None)
for name in ("eager.py", "lazy.py", "explicit.py", "filter.py"):
    result = subprocess.run([sys.executable, "-B", "-X", "lazy_imports=normal", str(root/name)], cwd=root, env=env, capture_output=True, text=True, timeout=10)
    if result.returncode:
        sys.stderr.write(result.stderr)
        raise SystemExit(f"FAIL: {name}")
    print(result.stdout, end="", flush=True)
print("PASS: eager control, deferred registration, explicit initialization, eager filter", flush=True)
