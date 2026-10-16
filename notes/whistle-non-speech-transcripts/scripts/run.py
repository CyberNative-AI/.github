"""Runner: tiny on-device ASR on non-speech audio.

Runs inside python:3.12-slim with the CPU-only venv mounted at /b/venv, network none.
Writes one JSONL per arm under OUT. Each row: id, set, text, sec, err.

usage: python run.py MANIFEST OUT ARM [ARM ...] [--limit N]
arms: W_en W_auto T_tiny T_base M_tiny VAD TOOL_W_en TOOL_T_tiny
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import soxr

SR = 16000
MAX_ERR_FRAC = 0.02  # frozen abort: an arm with >2% errors is INVALID


def load(path: str) -> np.ndarray:
    if path.startswith("synth:"):
        return np.load(path[6:]).astype(np.float32)
    audio, sr = sf.read(path, dtype="float32", always_2d=False)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != SR:
        audio = soxr.resample(audio, sr, SR, quality="HQ")
    return np.ascontiguousarray(audio, dtype=np.float32)


def arm_fn(arm: str):
    if arm in ("W_en", "W_auto"):
        import needle
        w = needle.Whistle()
        lang = "en" if arm == "W_en" else None
        return lambda a: w.transcribe(a, language=lang)["text"]
    if arm in ("T_tiny", "T_base"):
        import torch
        import whisper
        torch.set_num_threads(int(os.environ.get("THREADS", "4")))
        model = whisper.load_model(arm.split("_")[1], device="cpu")

        def t(a):
            torch.manual_seed(0)  # temperature fallback samples; seed per clip
            return model.transcribe(a, language="en", fp16=False)["text"].strip()
        return t
    if arm == "M_tiny":
        import moonshine_voice as mv
        path, march = mv.get_model_for_language("en", mv.ModelArch.TINY_STREAMING)
        m = mv.Transcriber(model_path=path, model_arch=march)
        return lambda a: " ".join(l.text.strip() for l in m.transcribe_without_streaming(a.tolist(), SR).lines).strip()
    if arm == "VAD":
        import torch
        from silero_vad import get_speech_timestamps, load_silero_vad
        vad = load_silero_vad()
        return lambda a: json.dumps(get_speech_timestamps(torch.from_numpy(a), vad, sampling_rate=SR))
    raise SystemExit(f"unknown arm {arm}")


def run_audio(manifest, out: Path, arm: str):
    fn = arm_fn(arm)
    rows, errs = [], 0
    path = out / f"{arm}.jsonl"
    done = set()
    if path.exists():  # resume: keep rows already written, count their errors
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            done.add(r["id"])
            rows.append(r)
            errs += bool(r["err"])
    with open(path, "a", encoding="utf-8") as fh:
        for item in manifest:
            if item["id"] in done:
                continue
            t0 = time.perf_counter()
            try:
                text, err = fn(load(item["path"])), None
            except Exception as e:  # recorded, counted against the abort
                text, err = None, f"{type(e).__name__}: {e}"[:300]
                errs += 1
            row = {"id": item["id"], "set": item["set"], "text": text,
                   "sec": round(time.perf_counter() - t0, 4), "err": err}
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            rows.append(row)
    return rows, errs


def run_tool(out: Path, arm: str):
    """Feed the source arm's non-empty transcripts to the vendor smart_home agent."""
    from needle.environments import smart_home
    import needle
    agent = needle.Needle(tools=smart_home.TOOLS, system=smart_home.SYSTEM, stateless=True)
    src = arm.split("_", 1)[1]
    rows, errs = [], 0
    with open(out / f"{src}.jsonl", encoding="utf-8") as fh:
        srows = [json.loads(l) for l in fh]
    # positive control: the vendor's own frozen acceptance prompts
    probes = [{"id": f"ctl{i}", "set": "tool_ctl", "text": c["query"], "category": c.get("category"),
               "expect_calls": len(c["calls"])} for i, c in enumerate(smart_home.TEST_CASES)]
    probes += [r for r in srows if r["text"]]
    with open(out / f"{arm}.jsonl", "w", encoding="utf-8") as fh:
        for r in probes:
            try:
                resp, err = agent.complete(r["text"]), None
            except Exception as e:
                resp, err = None, f"{type(e).__name__}: {e}"[:300]
                errs += 1
            row = {"id": r["id"], "set": r["set"], "text": r["text"], "err": err,
                   "category": r.get("category"), "expect_calls": r.get("expect_calls"),
                   "calls": (resp or {}).get("function_calls"), "confidence": (resp or {}).get("confidence")}
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            rows.append(row)
    return rows, errs


def main():
    args = sys.argv[1:]
    limit = None
    if "--limit" in args:
        i = args.index("--limit")
        limit = int(args[i + 1])
        del args[i:i + 2]
    manifest_path, out, arms = args[0], Path(args[1]), args[2:]
    out.mkdir(parents=True, exist_ok=True)
    manifest = [json.loads(l) for l in open(manifest_path, encoding="utf-8")]
    if limit:
        manifest = manifest[:limit]
    status = {}
    for arm in arms:
        t0 = time.time()
        rows, errs = run_tool(out, arm) if arm.startswith("TOOL_") else run_audio(manifest, out, arm)
        frac = errs / max(1, len(rows))
        status[arm] = {"n": len(rows), "errors": errs, "err_frac": round(frac, 4),
                       "invalid": frac > MAX_ERR_FRAC, "wall_s": round(time.time() - t0, 1)}
        print(arm, status[arm], flush=True)
    with open(out / f"status-{'-'.join(arms)}.json", "w") as fh:
        json.dump(status, fh, indent=1)


if __name__ == "__main__":
    main()
