# Rerunning the Timestral post-release check

Everything here ran on 24 October 2026 in a CPU-only Docker container (6 CPUs, 12 GiB, no network during the
model runs), Python 3.12. The full run of all models on both windows took about 28 minutes.

## Files

| Path | What it is |
|---|---|
| `PROTOCOL.md` | The protocol written before any October or September forecast; publication changes listed at its top |
| `src/install.sh` | Installs the pinned stack into `/opt/env` and downloads the pinned model revisions into `/opt/hf` |
| `src/prep.py` | Builds the frames from the EIA-930 CSVs and the Wikimedia pageviews API (stdlib only) |
| `src/run.py`, `src/run_all.sh` | One model on one window and domain; the loop over all of them |
| `src/score.py` | Scores every forecast; writes the JSON in `out/score-all.json` |
| `src/checks.py` | The alignment, same-input, spot-row and outlier checks; writes `out/checks-fresh.json` |
| `data/frames.json.gz` | The exact inputs we used: every series, window and exclusion reason |
| `env-freeze.txt` | `pip freeze` of the environment that ran |
| `out/score-all.json` | Scorer output: tables, pairwise ratios with intervals, per-series MASE, leakage probe |
| `out/forecasts.sha256` | SHA-256 of each raw forecast file (34 MB, not included) |
| `out/run.log` | One line per model run: forecast count, non-finite count, wall seconds |
| `recount/` | Our independent recount scripts and their output |

`data/frames.json.gz` decompresses to `frames.json` with SHA-256
`287c8597331bea61f189e64ff118c1afaf0ee2007cfb021a1915adb781c0cc10`. Changes from the files that ran: the first
docstring line of each script, and `prep.py` now reads the EIA CSVs from `raw/` beside the scripts' parent
directory instead of a directory on our machine. Nothing else.

## Commands

These are the commands that ran, with our directories replaced by `$PWD/...`. The scripts expect fixed paths
inside the container: `/opt/src` (this `src/`), `/opt/data` (the frames), `/opt/env` and `/opt/hf` (the
environment and weights that `install.sh` creates) and `/opt/out` (forecasts). The image was `python:3.12-slim`,
digest `python@sha256:05cda9777409a9c3ffddd94a4c476b79f0769a0b4857f0c7ed9226b6800b0d6f` (amd64).

```sh
IMG=python@sha256:05cda9777409a9c3ffddd94a4c476b79f0769a0b4857f0c7ed9226b6800b0d6f
mkdir -p data2 env hf fc
gunzip -c data/frames.json.gz > data2/frames.json

# 1. environment and pinned weights (needs network)
docker run --rm --cpus 4 --memory 6g --user 1000:1000 -e HOME=/tmp \
  -v "$PWD/env:/opt/env" -v "$PWD/hf:/opt/hf" -v "$PWD/src:/opt/src:ro" \
  $IMG sh /opt/src/install.sh

# 2. every forecast for the October (FRESH) and September (PRE) windows, no network (about 28 min on 6 CPUs)
docker run --rm --cpus 6 --memory 12g --network none --user 1000:1000 \
  -e HOME=/tmp -e HF_HUB_OFFLINE=1 -e NT=6 --tmpfs /tmp:rw,exec,size=2g \
  -v "$PWD/env:/opt/env:ro" -v "$PWD/hf:/opt/hf:ro" -v "$PWD/src:/opt/src:ro" \
  -v "$PWD/data2:/opt/data:ro" -v "$PWD/fc:/opt/out" \
  $IMG sh /opt/src/run_all.sh /opt/out FRESH PRE

# 3. scores (stdout is the JSON)
docker run --rm --read-only --network none --user 1000:1000 -e HOME=/tmp --tmpfs /tmp \
  -v "$PWD/env:/opt/env:ro" -v "$PWD/src:/opt/src:ro" -v "$PWD/data2:/opt/data:ro" -v "$PWD/fc:/opt/out:ro" \
  $IMG /opt/env/venv/bin/python -I /opt/src/score.py /opt/out FRESH PRE > my-score-all.json
```

`src/checks.py` reads an October-only score file at `/opt/score/score-fresh.json` (run `score.py /opt/out FRESH`
and mount its directory at `/opt/score`) and prints the checks JSON.

On 24 October we reran step 3 with the published `src/` against our forecasts (whose hashes are in
`out/forecasts.sha256`): the output was byte-identical to `out/score-all.json`
(SHA-256 `815de26db97bf16144bdb66556628e06a1b80ac1518ed7269d26b54852aefd2a`). We have not rerun steps 1 and 2
from this copy; forecasts on other hardware can differ in the last digits.

The recount scripts need only Python's standard library:

```sh
python3 -I recount/recount.py out/score-all.json
python3 -I recount/mase_recount.py data2/frames.json fc out/score-all.json   # needs the raw forecasts from step 2 in ./fc
```

## Rebuilding the inputs

`prep.py` downloads the Wikipedia series itself. For grid demand, download
`EIA930_BALANCE_2026_Jan_Jun.csv` and `EIA930_BALANCE_2026_Jul_Dec.csv` from
`https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/` into `raw/`, then run `python3 src/prep.py`. The
July–December file we used had `Last-Modified: Fri, 23 Oct 2026 14:41:03 GMT`; EIA updates it and may revise
recent values, so a later download will not give the same frames. The SHA-256 of each source file we used is in
`frames.json` under `sources`.
