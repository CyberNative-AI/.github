"""Build the manifests (host python, numpy from the venv).

usage: python manifest.py DATA_DIR OUT_DIR
Writes synth/*.npy, manifest-synth.jsonl, manifest-esc50.jsonl, manifest-speech.jsonl, manifest-pilot.jsonl.
"""
import csv
import json
import random
import sys
from pathlib import Path

import numpy as np

SEED = 13918
SR = 16000


def dbfs(x, level):
    rms = np.sqrt(np.mean(x ** 2)) or 1.0
    return x * (10 ** (level / 20) / rms)


def pink(n, rng):
    f = np.fft.rfftfreq(n, 1 / SR)
    spec = rng.standard_normal(len(f)) + 1j * rng.standard_normal(len(f))
    spec[1:] /= np.sqrt(f[1:])
    spec[0] = 0
    return np.fft.irfft(spec, n)


def hum(n, base):
    t = np.arange(n) / SR
    return sum(np.sin(2 * np.pi * base * k * t) / k for k in (1, 2, 3, 5))


def main():
    data, out = Path(sys.argv[1]), Path(sys.argv[2])
    rng = np.random.default_rng(SEED)
    sd = out / "synth"
    sd.mkdir(parents=True, exist_ok=True)
    n5 = 5 * SR
    synth = {
        "zeros_1s": np.zeros(SR), "zeros_5s": np.zeros(n5), "zeros_30s": np.zeros(30 * SR),
        "white_-90dB_5s": dbfs(rng.standard_normal(n5), -90),
        "white_-60dB_5s": dbfs(rng.standard_normal(n5), -60),
        "white_-40dB_5s": dbfs(rng.standard_normal(n5), -40),
        "white_-20dB_5s": dbfs(rng.standard_normal(n5), -20),
        "pink_-40dB_5s": dbfs(pink(n5, rng), -40),
        "pink_-20dB_5s": dbfs(pink(n5, rng), -20),
        "hum60_-30dB_5s": dbfs(hum(n5, 60), -30),
        "hum50_-30dB_5s": dbfs(hum(n5, 50), -30),
        "pink_-40dB_30s": dbfs(pink(30 * SR, rng), -40),
    }
    rows = []
    for k, v in synth.items():
        p = sd / f"{k}.npy"
        np.save(p, v.astype(np.float32))
        rows.append({"id": k, "set": "synth", "path": f"synth:/out/synth/{k}.npy"})
    write(out / "manifest-synth.jsonl", rows)

    meta = data / "esc/ESC-50-master/meta/esc50.csv"
    with open(meta, newline="") as fh:
        esc = sorted(csv.DictReader(fh), key=lambda r: r["filename"])
    rows = [{"id": r["filename"], "set": "esc50", "category": r["category"], "fold": int(r["fold"]),
             "path": f"/data/esc/ESC-50-master/audio/{r['filename']}"} for r in esc]
    write(out / "manifest-esc50.jsonl", rows)

    ls = data / "LibriSpeech/test-clean"
    utts = []
    for tf in sorted(ls.glob("*/*/*.trans.txt")):
        for line in tf.read_text().splitlines():
            uid, ref = line.split(" ", 1)
            utts.append({"id": uid, "set": "speech", "ref": ref,
                         "path": f"/data/LibriSpeech/test-clean/{tf.parent.relative_to(ls)}/{uid}.flac"})
    random.Random(SEED).shuffle(utts)
    write(out / "manifest-speech.jsonl", sorted(utts[:300], key=lambda r: r["id"]))
    # pilot: API/timing only; synthetic + 5 speech utterances NOT in the 300 sample; no ESC-50
    pilot = [{"id": k, "set": "synth", "path": f"synth:/out/synth/{k}.npy"} for k in ("zeros_5s", "pink_-20dB_5s")]
    write(out / "manifest-pilot.jsonl", pilot + utts[300:305])
    print(len(synth), len(esc), len(utts), "utterances total; sample 300")


def write(path, rows):
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
