"""Post-hoc path diagnostics (not part of the frozen verdict).

D1 vendor file path: needle.transcribe(<original 44.1 kHz ESC-50 wav>, language="en") on 100 seeded clips.
D2 loader control: 50 seeded LibriSpeech utterances upsampled 16k->44.1k (soxr), written as wav, read back through
   run.load() (44.1k->16k) and transcribed by Whistle en; WER vs reference.
usage: python diag.py OUT_DIR
"""
import json
import random
import sys
from pathlib import Path

import jiwer
import needle
import numpy as np
import soundfile as sf
import soxr
from whisper.normalizers import EnglishTextNormalizer

sys.path.insert(0, "/code")
from run import load  # noqa: E402

EN = EnglishTextNormalizer()
out = Path(sys.argv[1])
res = {}
esc = [json.loads(l) for l in open(out / "manifest-esc50.jsonl", encoding="utf-8")]
d1 = sorted(random.Random(139181).sample(esc, 100), key=lambda r: r["id"])
w = needle.Whistle()
rows = []
for r in d1:
    vendor = needle.transcribe(r["path"], language="en")["text"]
    mine = w.transcribe(load(r["path"]), language="en")["text"]
    rows.append({"id": r["id"], "vendor_path": vendor, "our_loader": mine})
res["D1"] = {"n": len(rows), "vendor_nonempty": sum(bool(EN(x["vendor_path"]).split()) for x in rows),
             "ours_nonempty": sum(bool(EN(x["our_loader"]).split()) for x in rows),
             "identical": sum(x["vendor_path"] == x["our_loader"] for x in rows)}
sp_all = [json.loads(l) for l in open(out / "manifest-speech.jsonl", encoding="utf-8")]
d2 = sorted(random.Random(139182).sample(sp_all, 50), key=lambda r: r["id"])
tmp = out / "diag_up"
tmp.mkdir(exist_ok=True)
refs, hyps, d2rows = [], [], []
for r in d2:
    a, sr = sf.read(r["path"], dtype="float32")
    up = soxr.resample(a, sr, 44100, quality="HQ")
    p = tmp / f"{r['id']}.wav"
    sf.write(p, up, 44100, subtype="PCM_16")
    t = w.transcribe(load(str(p)), language="en")["text"]
    refs.append(EN(r["ref"]))
    hyps.append(EN(t) or "<empty>")
    d2rows.append({"id": r["id"], "text": t})
res["D2"] = {"n": len(d2), "nonempty": sum(h != "<empty>" for h in hyps), "wer": round(jiwer.wer(refs, hyps), 4)}
json.dump({"summary": res, "D1_rows": rows, "D2_rows": d2rows}, open(out / "diag.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(res))
