# Reproduce

These commands rebuild the run from a fresh install on an x86-64 Linux machine with Docker. CPU only; no GPU is used.
Budget: a little over 4 hours of 6-CPU time for every arm, about 1 hour for the three verdict arms (Whistle English,
Whisper tiny, Silero VAD). Each stage has its own limits; see section 2.

## 0. Check the numbers without audio (a few minutes)

`results/raw/` holds every output row and the manifests, so the frozen scorer can rescore them directly:

```sh
python3.12 -m venv v && . v/bin/activate
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.11.0
pip install openai-whisper==20250625 jiwer==4.0.0
python scripts/score.py results/raw results/raw/repeat > rescore.json
python -c "import json; print(json.load(open('rescore.json')) == json.load(open('results/score-final.json')))"
```

It prints `True`. The confidence counts for the smart-home calls (1,951 transcripts sent, 1,780 calls; 16, 5 and 0 at
0.4, 0.5 and 0.7):

```sh
python -c "
import json
rows = [json.loads(l) for l in open('results/raw/TOOL_W_en.jsonl')]
c = [r['confidence'] or 0 for r in rows if r['set'] == 'esc50' and r['calls']]
print(sum(r['set'] == 'esc50' for r in rows), len(c), *(sum(v >= t for v in c) for t in (0.4, 0.5, 0.7)))"
```

## 1. Data (not redistributed)

Download into `work/data/` and check against `inputs.sha256`:

- ESC-50 (CC BY-NC 3.0): `https://github.com/karoldvl/ESC-50/archive/master.zip`, unzipped to `work/data/esc/ESC-50-master/`.
- LibriSpeech test-clean (CC BY 4.0): `https://www.openslr.org/resources/12/test-clean.tar.gz`, unpacked to
  `work/data/LibriSpeech/test-clean/`.

## 2. Limits, environment and weights

Every stage below runs in its own container through this `box` function. Each container gets a CPU limit, a memory
limit with swap off (`--memory-swap` equal to `--memory`), a process limit and a wall-time limit. `timeout` inside the
container stops the stage at its limit (exit code 124), and `--rm` removes the container when it ends. `--init` passes
Ctrl-C to the stage. If the `docker` client itself is killed, remove the container with `docker rm -f whistle-repro`.
Only the install and weight-fetch stages have network access.

```sh
mkdir -p work/data work/out work/home
# box SECONDS NETWORK CPUS MEMORY 'COMMAND'
box() {
  docker run --rm --init --name whistle-repro --network "$2" --cpus "$3" --memory "$4" --memory-swap "$4" \
    --pids-limit 4096 -e HOME=/b/home -e NEEDLE_TELEMETRY=0 -e DO_NOT_TRACK=1 -e HF_HUB_DISABLE_TELEMETRY=1 \
    -v "$PWD/work:/b" -v "$PWD/work/data:/data:ro" -v "$PWD/work/out:/out" -v "$PWD:/code:ro" \
    python:3.12-slim timeout -k 30 "$1" sh -c "$5"
}
```

Install the 46 pinned packages from `env-freeze.txt` exactly, without dependency resolution: the two torch lines from the
PyTorch CPU index, the rest from PyPI (limit 30 min, 4 CPUs, 6 GB):

```sh
grep '^torch' env-freeze.txt > work/req-torch.txt && grep -v '^torch' env-freeze.txt > work/req-pypi.txt
box 1800 bridge 4 6g '
  pip install -q uv && uv venv /b/venv --python /usr/local/bin/python3.12 -q &&
  uv pip install -q --python /b/venv/bin/python --no-deps --index-url https://download.pytorch.org/whl/cpu -r /b/req-torch.txt &&
  uv pip install -q --python /b/venv/bin/python --no-deps -r /b/req-pypi.txt &&
  uv pip freeze --python /b/venv/bin/python | diff - /code/env-freeze.txt && echo "freeze matches"'
```

It prints `freeze matches`. (`uv pip check` will note that openai-whisper declares `triton` on x86-64 Linux; the frozen
environment has no triton, and none is needed on CPU.) Then fetch the weights once (limit 20 min, 4 CPUs, 6 GB), and
check them against `weights.sha256`:

```sh
box 1200 bridge 4 6g '. /b/venv/bin/activate && python -c "
import whisper, needle, moonshine_voice as mv
from needle.environments import smart_home
from silero_vad import load_silero_vad
for s in (\"tiny\", \"base\"): whisper.load_model(s, device=\"cpu\")
mv.get_model_for_language(\"en\", mv.ModelArch.TINY_STREAMING)
needle.Whistle(); needle.Needle(tools=smart_home.TOOLS, system=smart_home.SYSTEM, stateless=True); load_silero_vad()"'
```

## 3. Manifests

Network off from here on (limit 15 min, 2 CPUs, 4 GB):

```sh
box 900 none 2 4g '. /b/venv/bin/activate && python /code/scripts/manifest.py /data /out &&
  cat /out/manifest-synth.jsonl /out/manifest-speech.jsonl /out/manifest-esc50.jsonl > /out/manifest-main.jsonl &&
  python /code/scripts/score.py --repeat-ids /out/manifest-esc50.jsonl > /out/repeat-ids.txt &&
  python -c "import json; ids = set(open(\"/out/repeat-ids.txt\").read().split()); open(\"/out/manifest-repeat.jsonl\", \"w\").writelines(l for l in open(\"/out/manifest-esc50.jsonl\") if json.loads(l)[\"id\"] in ids)"'
(cd work/out && sha256sum manifest-*.jsonl)
```

The manifest hashes must equal those in `inputs.sha256`, and `manifest-repeat.jsonl` must equal `results/raw/manifest-repeat.jsonl`.

## 4. Run and score

One container per arm, network off, 6 CPUs, 10 GB, swap off, at most 3 hours each:

```sh
A='. /b/venv/bin/activate && cd /out && export HF_HUB_OFFLINE=1 THREADS=6 && python /code/scripts/run.py'
for a in VAD W_en T_tiny W_auto M_tiny T_base; do box 10800 none 6 10g "$A /out/manifest-main.jsonl /out/main $a" || break; done
box 10800 none 6 10g "$A /out/manifest-main.jsonl /out/main TOOL_W_en TOOL_T_tiny"
for a in VAD W_en T_tiny; do box 3600 none 6 10g "$A /out/manifest-repeat.jsonl /out/repeat $a" || break; done
box 900 none 2 4g 'cp /out/manifest-*.jsonl /out/main/ && . /b/venv/bin/activate && python /code/scripts/score.py /out/main /out/repeat > /out/main/score.json'
```

For the verdict only, run the first loop with `VAD W_en T_tiny` (about 1 hour) and score with
`python /code/scripts/score.py /out/main > /out/main/score.json`.

Our first run took about 13 min for W_en, 1 min for VAD, 46 min for T_tiny, 14 min for W_auto, 13 min for M_tiny, about
2 hours for T_base and 31 min for the two smart-home arms. Both of our runs used the 10 GB memory limit above; the
protocol had planned 8 GB.

Run the arms one at a time; running them in parallel in one container slowed Whistle by more than 50× (see
`protocol/AMENDMENT-01.md`). `run.py` skips clips already written, so if an arm stops at its limit (exit code 124) or
is interrupted, the same command resumes it.

## 5. Compare with our rows

```sh
python scripts/rerun_compare.py results/raw results/score-verdict-arms.json work/out/main > compare.json
python -c "import json; d = json.load(open('compare.json')); print(d['all_rows_identical'], d['rerun_pass'])"
```

Rows are matched by clip id on text and error; latency differs run to run. Our own second run from a fresh install
printed `True True`, and its outputs are in `results/rerun/`.
