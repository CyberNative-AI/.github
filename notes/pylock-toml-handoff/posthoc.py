"""Post-hoc probe (not in the frozen protocol): installer MUST-error checks on CPython 3.10.
P0 unmodified uv-fixture/S0 pylock (control), P1 + top-level environments python>=3.12,
P3 + per-package requires-python >=3.12 on click. Spec: each of P1/P3 MUST raise an error."""
import json, sys
sys.argv = [sys.argv[0], "3.10", "posthoc-3.10"]
sys.path.insert(0, "/x")
import consume as c
from pathlib import Path
c.OUT.mkdir(parents=True, exist_ok=True); c.SCR.mkdir(parents=True, exist_ok=True)
rows = []
for p in sorted(Path("/w/posthoc").glob("P*.toml")):
    for consumer in ("pip", "uv-install", "uv-sync", "pipenv"):
        r = c.run_pylock(p, p.stem, "S0", consumer, [], "")
        rows.append({k: r.get(k) for k in ("cell", "rc", "installed")} | {"tail": r["tail"][-300:]})
(c.OUT / "posthoc.jsonl").write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in rows))
for x in rows: print(x["rc"], x["cell"], sorted(x["installed"] or {}))
