# pgrust 0.4-beta cache modes: scripts and raw results

This folder is the record of our October 23-24 (UTC) runs, not a tested reproduction kit.
`src/pg_run.sh`, `src/pg_run_diag.sh`, `src/run_rep.sh` and `src/run_diag.sh` are the scripts that
ran inside the containers, unchanged except for their comment lines. The `docker run` arguments
below describe the measured containers. `src/fetch-inputs.sh` and `src/check_inputs.py` were written afterwards for this
folder: we checked each URL and every sha256 in `inputs.sha256` against our copies, but have not
run the script end to end. The scripts run PostgreSQL-compatible servers with trust
authentication inside a throwaway container; never point them at a real server.

## Inputs

`bash src/fetch-inputs.sh DIR` downloads, into `DIR/dl` and `DIR/data`, the pgrust v0.4-beta
x86_64 tarball from pgrust.com and partitions `hits_0` to `hits_15` from ClickBench's dataset
host (about 2.3 GB), and, into `upstream/`, `create.sql` and `queries.sql` from the head commit
of ClickHouse/ClickBench#2751 (`deabb4a5`). It checks all 19 files against `inputs.sha256` and
writes `src/queries-determinized.sql` with `src/determinize.py`. The ClickBench files are not
copied here because ClickBench is licensed CC BY-NC-SA 4.0.

## How the runs were started

Each load was one container: `debian:13-slim` (image
`sha256:133aec7ab1411181567fef7fc3f4512123e1f9660090b49851de4b698b4ff772`, amd64), this folder
mounted read-only at `/lab`, `DIR/dl` at `/dl` and `DIR/data` at `/data` (read-only), an empty
writable folder at `/scratch`, and `src/passwd` at `/etc/passwd` so that uid 1000 has a name:

```sh
docker run --rm --network=none --cpus=6 --memory=16g --memory-swap=16g --pids-limit=4096 \
  --user=1000:1000 \
  --volume="$PWD/src/passwd:/etc/passwd:ro" \
  --volume="DIR/dl:/dl:ro" --volume="DIR/data:/data:ro" \
  --volume="$PWD:/lab:ro" --volume="SCRATCH:/scratch" \
  --env=THREADS=6 --env=MEM_KB=12582912 \
  debian:13-slim bash /lab/src/run_rep.sh
```

Loads A and B ran `run_rep.sh` (arms T, D and S below) in two separate containers, each with a
fresh `initdb` and load. Load C ran `run_diag.sh` the same way. Results were copied from
`/scratch/out` into `out/rep-a`, `out/rep-b` and `out/diag`. Loads A and B took 15 and 19
minutes, load C 10.

- **T** (timing): for each mode `full rows granule off` and each of the 43 queries, restart the
  server, run the query 3 times with `\timing`, then `EXPLAIN (ANALYZE, VERBOSE)`. Records in
  `T.jsonl`, EXPLAINs in `explain-t-*`.
- **D** (answers): the same loop over `queries-determinized.sql`, 2 runs per restart. Records in
  `D.jsonl`, EXPLAINs in `explain-d-*`.
- **S** (staleness): per mode, warm Q1 and Q20, insert or delete rows, rerun them on the same
  server, then recount after a restart with every cache off. Records in `S.jsonl`.
- **Load C**: arm T only, with modes `full+nodict rows+nodict granule full`; `+nodict` adds
  `pgrust.dict_filter_cache=off`. Records in `diag/X.jsonl`, EXPLAINs in `explain-x-*`.

Each `run` record holds the mode the server reported (`mode_shown`), the query number (from 0),
the run (1 = cold), psql's time in ms, the exit code, an error flag and the first 16 hex digits
of the sha256 of the result text.

## Recomputing the numbers

```sh
python3 -I src/score.py out           # rewrites out/score.json byte for byte
python3 -I src/score_diag.py out/diag # prints out/diag/summary.txt
python3 -I src/recount.py out         # prints out/recount.txt
```

`score.py` scores loads A and B (it reads only folders named `rep-*` that contain `DONE`).
`recount.py` is a second count of the same numbers written without looking at `score.py`'s
code: hot and cold geomean ratios for every mode, the Q20-Q22 swap, per-query hot times, EXPLAIN
granule readouts, answer hashes against `off` and staleness checks. `out/static-strings.tsv`
holds the `strings` counts for the beta binary.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai.
