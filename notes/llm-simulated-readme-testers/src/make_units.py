"""Extract scored units from runs/ and controls/, assign seeded random ids, write adjudication batches.
Scored unit: A2 = text after the PROBLEMS heading; A1/A0/PC = whole reply. Mapping kept in adjudication/units_key.json."""
import hashlib, json, random, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS, CTRL, ADJ = ROOT / "runs", ROOT / "controls", ROOT / "adjudication"
ADJ.mkdir(exist_ok=True)

def problems_section(text):
    m = list(re.finditer(r"^[#*\s]*PROBLEMS\b.*$", text, flags=re.M | re.I))
    if not m:
        return None, None
    cut = m[-1].end()
    return text[cut:].strip(), text[:m[-1].start()].strip()

units = []
for f in sorted(RUNS.glob("*.md")):
    arm, version, rk = f.stem.split("__")
    text = f.read_text(encoding="utf-8")
    if arm == "A2_simulated":
        scored, narration = problems_section(text)
        if scored is None:
            raise SystemExit(f"no PROBLEMS heading in {f.name}")
        units.append({"source": f.name, "arm": arm, "version": version, "run": rk, "part": "problems", "text": scored})
        units.append({"source": f.name, "arm": arm, "version": version, "run": rk, "part": "narration", "text": narration})
    else:
        units.append({"source": f.name, "arm": arm, "version": version, "run": rk, "part": "list", "text": text.strip()})
for f in sorted(CTRL.glob("PC*.md")):
    units.append({"source": f.name, "arm": "control", "version": f.stem, "run": "-", "part": "problems", "text": f.read_text(encoding="utf-8").strip()})

rng = random.Random(13683)
ids = rng.sample(range(1000, 10000), len(units))
for u, i in zip(units, ids):
    u["uid"] = f"U{i}"
    u["sha256"] = hashlib.sha256(u["text"].encode()).hexdigest()
rng.shuffle(units)
key = [{k: u[k] for k in ("uid", "source", "arm", "version", "run", "part", "sha256")} for u in units]
(ADJ / "units_key.json").write_text(json.dumps(key, indent=1) + "\n", encoding="utf-8")
BATCH = 6
for b in range(0, len(units), BATCH):
    chunk = units[b:b + BATCH]
    body = "\n\n".join(f"=== CRITIQUE {u['uid']} START ===\n{u['text']}\n=== CRITIQUE {u['uid']} END ===" for u in chunk)
    (ADJ / f"batch_{b // BATCH:02d}.md").write_text(body + "\n", encoding="utf-8")
print(len(units), "units;", (len(units) + BATCH - 1) // BATCH, "batches")
