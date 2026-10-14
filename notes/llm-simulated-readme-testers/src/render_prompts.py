"""Render arm prompts for a version: python3 render_prompts.py <arm_template> <package.md> <out>."""
import hashlib, sys
from pathlib import Path
t = Path(sys.argv[1]).read_text(encoding="utf-8"); p = Path(sys.argv[2]).read_text(encoding="utf-8")
assert t.count("{PACKAGE}") == 1
out = t.replace("{PACKAGE}", p); assert "{PACKAGE}" not in out
Path(sys.argv[3]).write_text(out, encoding="utf-8", newline="\n")
print(hashlib.sha256(out.encode()).hexdigest(), sys.argv[3])
