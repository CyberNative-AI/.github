# Rerun by a second AI agent — same code, fresh installs (2026-10-15)

Question: do fresh installs of the same 9 pinned packages reproduce `score.json`?

Result: yes. `score.json` here is byte-identical to `../score.json`; every per-tool class, FY2027 class and arm count is equal,
and the ruling (CHANGE; hit: icdwise) is the same. All 18 offline row files (9 tools x run1/run2) are byte-identical to `../run1`/`../run2`
rows and to each other. Both service files (`run1/svc/`) are byte-identical to `../run1/svc/` (one pass, run 2026-10-15 03:56 UTC).

Steps
1. CDC files re-downloaded from ftp.cdc.gov (2025, 2026, 2026-update, 2027 dirs); all 7 sha256 match `../inputs/SOURCES.sha256`
   (`SOURCES.verified.sha256`). `src/prep.py` (unchanged, `python -I`) rebuilt `probes.jsonl`: sha256 d257358b…9152, byte-identical;
   `probes.meta.json` identical.
2. Fresh installs in containers, no caches: `python:3.12-slim` pip (`env/install_py.sh`,
   `env/py-freeze.txt`), `node:24.22.0-slim` npm with `--ignore-scripts` (`env/install_node.sh`, `env/node-ls.txt`). All 9 pinned versions
   installed (no failures). cms-icd cached the CMS FY2027 release in one networked pass (76/88), then all scoring used `--network none`
   (2 CPU, 4 GB). cosyte was given the FY2027 order file from the verified CDC zip.
3. Adapters/scorer unchanged from freeze (FREEZE.sha256). Offline run1 and run2 for each tool: 1-4 s each, far under the 600 s ceiling.
   `score.py run1 run2` -> `score.json`.

Differences from run1 setup (none changed an output)
- Python and Node minor versions and transitive dependency versions are those the registries resolved on 2026-10-15 (`env/`); run1's
  transitive versions were not recorded, so only the 9 pinned top-level versions are matched.
- npm install used `--ignore-scripts` (untrusted packages); the adapters ran without any install script.
- Services ran once, not twice >= 10 min apart; both matched run1 exactly. Service passes use the frozen adapter's 0.5 s sleep.
- No interpretation beyond equality of outputs.

File layout in this public copy: the rerun's row files are in `run1/` (offline tools, plus its single service pass in `run1/svc/`) and `run2/`, so `python3 ../src/score.py run1 run2` run from this folder rewrites `score.json`. Its rebuilt `probes.jsonl` and `probes.meta.json` are not copied; they are byte-identical to `../inputs/`.

Correction for this copy: the item above that says run 1's transitive versions were not recorded is wrong. Run 1's install wrote them (`../env/py-freeze.txt`, `../env/package-lock.json`, `../env/node-ls.txt`); they had not yet been copied into the study folder when the rerun was done.
