# Reproduce: ECMWF open data, 12-bit precipitation and 0.1 mm rain products

This folder holds the plan we froze before the main run, its two amendments, the scripts, the image recipe and the
outputs behind the note. It does not hold the GRIB files. All inputs are ECMWF open data (CC BY 4.0) and the fetch
script downloads them again from ECMWF's Google Cloud mirror.

- `PROTOCOL.md`: the plan: arms, metrics, gates and decision rules, frozen on 2026-10-28 before the main run.
- `AMENDMENT-01.md`: a mechanics fix after the first run crashed on its first re-encode, before any metric existed.
- `AMENDMENT-02.md`: written after the results. It reports that one gate in the code was stricter than the plan's
  text, and gives the verdict under each. Read it before using the verdict.
- `src/fetch.py`: downloads `tp` (and the land-sea mask), or the parameters given with `--params`, by byte range,
  using ECMWF's published `.index` files.
- `src/analyse.py`: re-encodes the 15 and 19 October runs at 12 bits, computes every metric, gate and the verdict.
- `src/sim12_census.py`: applies the gate in question to every message and lists each failure.
- `src/sec5.py`: reads the packing header (GRIB2 section 5) of a parameter in any open-data run. Standard library only.
- `img/Dockerfile`, `img/WHEELS.sha256`: the analysis image (Python 3.12, ecCodes 2.50 from PyPI wheels).
- `out/result.json`: the output of `analyse.py` (primary evidence). `out/sim12-census.json`: the output of
  `sim12_census.py`. `out/RAW.sha256`: sha256 of every input file we used.
- `sd/`: the snow depth check. `sd/PRE-SD.md` is its plan, written before any snow values were decoded;
  `sd/AMENDMENT-SD-01.md` was written after the results. `src/sd_census.py` computes the planned measures and
  `src/sd_census_a1.py` adds the amendment's depth fix and exploratory split. `sd/out/sd-result.json` and
  `sd/out/sd-result-a1.json` are their outputs; `sd/out/RAW-SD.sha256` lists the three input files.

## Check the step in a file you use

```sh
python3 -I src/sec5.py 20261028 tp 6,24,48,72,144,240,360
```

It prints the binary scale factor `E` for each forecast step of that day's 00 UTC HRES run (AWS mirror; a run is kept
there for a limited time, so use a recent date). `tp` is in metres, so the step is 2^E m: `E = -12` is 0.244 mm. On
2026-10-29 at 02:55 UTC this printed `E = -14` (0.061 mm) at 6 h, `-13` (0.122 mm) at 24 h and `-12` (0.244 mm) at
48, 72, 144, 240 and 360 h for the 28 October run.

For snow depth, use `sd` instead of `tp`; `step_size` is printed in metres of water equivalent. On 2026-10-29 at
14:41 UTC, `python3 -I src/sec5.py 20261028 sd 0,24,144,240` printed `nbits` 9, `R` 0.0 and `step_size` 0.03125 at
each step; the same command for 20261015 printed `nbits` 16 and 0.000244140625.

## Rerun the analysis

Needs Docker, about 3 GB of disk for inputs, 4 CPUs and 8 GB of memory; the analysis took 12 minutes on our machine.
Download the eight wheels named in `img/WHEELS.sha256` from PyPI into `img/` and check them with
`sha256sum -c WHEELS.sha256` (run inside `img/`). Then, from this folder:

```sh
mkdir -p raw run
for D in 20261015 20261019 20261028; do
  python3 -I src/fetch.py raw $D oper $( (seq 0 6 144; seq 150 6 360) | paste -sd, ) --lsm
  python3 -I src/fetch.py raw $D enfo $(seq -s, 0 6 144)
done
(cd raw && sha256sum -c ../out/RAW.sha256)
docker build -t ecmwf-12bit-tp img
docker run --rm --network none --read-only --tmpfs /tmp --user $(id -u):$(id -g) \
  -v "$PWD/raw:/raw:ro" -v "$PWD/src:/src:ro" -v "$PWD/run:/out" \
  ecmwf-12bit-tp python -I /src/analyse.py /raw /out/result.json
docker run --rm --network none --read-only --tmpfs /tmp --user $(id -u):$(id -g) \
  -v "$PWD/raw:/raw:ro" -v "$PWD/src:/src:ro" ecmwf-12bit-tp python -I /src/sim12_census.py > run/sim12-census.json
```

The mirror kept the 15 October files on 2026-10-29. If it no longer has a run, the fetch fails for that run;
`RAW.sha256` names every file we used. The ensemble dither arm uses a fixed seed, so `run/result.json` should equal
`out/result.json` on the same inputs and package versions.

## Rerun the snow depth check

Same image. From this folder, about 3 MB of downloads and under a minute of analysis:

```sh
mkdir -p run
for D in 20261015 20261019 20261028; do
  python3 -I src/fetch.py sd/fetch $D oper 24 --params sd,rsn,lsm
  mkdir -p sd/raw/$D && cp sd/fetch/$D/oper/24.grib2 sd/raw/$D/
done
(cd sd && sha256sum -c out/RAW-SD.sha256)
docker run --rm --network none --read-only --tmpfs /tmp --user $(id -u):$(id -g) \
  -v "$PWD/sd/raw:/raw:ro" -v "$PWD/src:/src:ro" -v "$PWD/run:/out" \
  ecmwf-12bit-tp python -I /src/sd_census.py /raw /out/sd-result.json
docker run --rm --network none --read-only --tmpfs /tmp --user $(id -u):$(id -g) \
  -v "$PWD/sd/raw:/raw:ro" -v "$PWD/src:/src:ro" -v "$PWD/run:/out" \
  ecmwf-12bit-tp python -I /src/sd_census_a1.py /raw /out/sd-result-a1.json
```

`run/sd-result.json` and `run/sd-result-a1.json` should equal the files in `sd/out/`.

## Differences from the files we ran

We removed internal labels and paths from seven files and added one option to `fetch.py`. Nothing else changed:

- `PROTOCOL.md`: an internal project code in the title, the owner line and a local storage path.
- `AMENDMENT-01.md`: internal job-queue wording and a local test script path.
- `src/analyse.py` and `src/sim12_census.py`: an internal project code and image tag in the first docstring line.
- `src/sd_census.py` and `src/sd_census_a1.py`: an internal project code in the first docstring line.
- `sd/PRE-SD.md`: an internal project code in the title and first line, an internal image tag and an internal task
  reference.
- `src/fetch.py`: we added `--params` after the runs, so that one script fetches the snow depth inputs. Without it the
  script behaves as before. With `--params sd,rsn,lsm` it downloaded the three files in `sd/out/RAW-SD.sha256` byte for
  byte on 2026-10-29.

The sha256 values quoted inside the amendments are those of the files we ran. `analyse.py` there is `8b34233b…` and
`sim12_census.py` is `b5ed3f12…`; the public copies differ only in that first line, so their line numbers match.
`sd/AMENDMENT-SD-01.md` is unchanged. The snow scripts we ran are `37f3098c…` (`sd_census.py`) and `84fbbb75…`
(`sd_census_a1.py`); the plan we ran was `d90995e0…`.

The scripts and our text are under the MIT licence (`LICENSE`). The files in `out/` are derived from ECMWF open data
(CC BY 4.0); the attribution is at the end of the [note](../README.md). `SHA256SUMS` lists every file in this folder.
