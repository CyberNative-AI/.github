# GVS5H regrade: judge, controls and per-row verdicts

This folder is the record of our October 25 (UTC) run. The code in `src/` is what ran,
unchanged except for module docstrings and one Dockerfile comment; `src/merge.py` and
`THIRD-PARTY-NOTICES.md` were added for this copy. The stored solutions and the
LiveCodeBench tests are not here; the commands below rebuild both, and `out/inputs.sha256` has
the hashes we got.

## Files

- `src/Dockerfile`: the judge image. `python:3.12-slim` pinned by digest, plus numpy 2.2.5 and
  scipy 1.15.2, the versions in LiveCodeBench's `uv.lock` (90 stored solutions import numpy,
  2 import scipy).
- `src/extract.py`: builds `records.jsonl` from a GVS5H clone: one row per arm, pass and
  problem, with the stored code, the paper's verdict (`reported`) and the stock evaluator's
  verdict (`stock`).
- `src/judge.py`: `prep` turns the 100 LiveCodeBench rows into per-problem test files; `judge`
  runs every test of every record as a fresh subprocess and writes one verdict line per record
  (PASS, WA, RE, TLE or NOCODE, with the slowest test's time in `max_t`).
- `src/checkers.py`: the contest-rule checkers for abc385_f, abc396_e, arc190_a and arc195_c,
  written from the problem statements.
- `src/controls.py`: the checks run before judging; `out/controls-run.json` is its output.
- `src/score.py`: means, agreement with the paper, the bootstrap interval and the pre-set rule.
- `src/merge.py`: builds the two merged columns below from the raw judge outputs.
- `out/verdicts.jsonl`: all 2,500 records at 6 s per test, 5 worker processes.
- `out/verdicts_t6w1.jsonl`: the 21 records that timed out, judged again at 6 s with one worker.
  `out/verdicts_t6fix.jsonl` is `verdicts.jsonl` with the 2 records that passed there replaced.
- `out/verdicts_t18.jsonl`: the same 21 records at 18 s. `out/verdicts_t18full.jsonl` is
  `verdicts.jsonl` with those 21 lines replaced.
- `out/score-t6.json`, `out/score-t6fix.json`, `out/score-t18.json`: `score.py` output for the
  three columns in the note. `score-t6.json` reports `INVALID (G1)`: the check described in the
  note's "Order of work" failed on that column.

Error excerpts in the verdict files quote the stored solutions, which are GVS5H run data
(CC BY 4.0); see [`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md).

## Rescore the published verdicts

These need only `records.jsonl`, rebuilt from GVS5H, and the files in `out/`. They run no
solution.

```sh
git clone https://github.com/slee-persis/GVS5H gvs5h
git -C gvs5h checkout 707e21296bfa032250f10bdde4afaff7ec998f71
mkdir -p data
python3 -I src/extract.py gvs5h data/records.jsonl
sha256sum data/records.jsonl                      # compare with out/inputs.sha256
python3 -I src/score.py data/records.jsonl out/verdicts.jsonl out/verdicts_t18.jsonl | cmp - out/score-t6.json
python3 -I src/score.py data/records.jsonl out/verdicts_t6fix.jsonl out/verdicts_t18.jsonl | cmp - out/score-t6fix.json
python3 -I src/score.py data/records.jsonl out/verdicts_t18full.jsonl | cmp - out/score-t18.json
mkdir -p merged && cp out/verdicts.jsonl out/verdicts_t6w1.jsonl out/verdicts_t18.jsonl merged/
python3 -I src/merge.py merged data/records.jsonl
cmp merged/verdicts_t6fix.jsonl out/verdicts_t6fix.jsonl && cmp merged/verdicts_t18full.jsonl out/verdicts_t18full.jsonl
```

Every `cmp` prints nothing when the bytes match. `score.py` does not check that a verdict file
is complete; `merge.py` does, for `verdicts.jsonl`.

## Judge again from scratch

This runs every stored solution. It writes to a new, empty `fresh/` directory and leaves `out/`
untouched. `judge.py` resumes: it skips any record already in its output file, so never point
it at `out/`. The commands are equivalent to what we ran; our paths differed.

```sh
curl -LO https://huggingface.co/datasets/livecodebench/code_generation_lite/resolve/main/test5.jsonl
curl -LO https://huggingface.co/datasets/livecodebench/code_generation_lite/resolve/main/test6.jsonl
python3 -I -c '
import json
ids = {json.loads(l)["qid"] for l in open("data/records.jsonl")}
with open("data/lcb100.jsonl", "w", encoding="utf-8", newline="\n") as o:
    for f in ("test5.jsonl", "test6.jsonl"):
        for l in open(f, encoding="utf-8"):
            if json.loads(l)["question_id"] in ids:
                o.write(l if l.endswith("\n") else l + "\n")
'
sha256sum data/lcb100.jsonl test5.jsonl test6.jsonl   # compare with out/inputs.sha256
mkdir fresh && chmod 777 fresh
docker build -t gvs5h-judge src/
R="docker run --rm --network none --read-only --user 1000:1000 --tmpfs /tmp:exec,size=2g --cpus 6 --memory 12g \
   -v $PWD/src:/src:ro -v $PWD/data:/data:ro -v $PWD/fresh:/out gvs5h-judge"
$R python3 -I /src/judge.py prep /data/lcb100.jsonl /out/tests
$R sh -c 'python3 -I /src/controls.py /out/tests > /out/controls-run.json'
$R python3 -I /src/judge.py judge /data/records.jsonl /out/tests /out/verdicts.jsonl --workers 5 --timeout 6
python3 -I -c '
import json
keys = {json.loads(l)["key"] for l in open("fresh/verdicts.jsonl") if json.loads(l)["verdict"] == "TLE"}
open("data/tle.jsonl", "w").writelines(l for l in open("data/records.jsonl") if json.loads(l)["key"] in keys)
'
$R python3 -I /src/judge.py judge /data/tle.jsonl /out/tests /out/verdicts_t18.jsonl --workers 5 --timeout 18
$R python3 -I /src/judge.py judge /data/tle.jsonl /out/tests /out/verdicts_t6w1.jsonl --workers 1 --timeout 6
python3 -I src/merge.py fresh data/records.jsonl
python3 -I src/score.py data/records.jsonl fresh/verdicts.jsonl fresh/verdicts_t18.jsonl > fresh/score-t6.json
python3 -I src/score.py data/records.jsonl fresh/verdicts_t6fix.jsonl fresh/verdicts_t18.jsonl > fresh/score-t6fix.json
python3 -I src/score.py data/records.jsonl fresh/verdicts_t18full.jsonl > fresh/score-t18.json
```

A fresh run will not match our files byte for byte: timeouts depend on the machine and on its
load, and on a faster CPU fewer solutions time out at 6 s. We ran on an AMD Ryzen 7 3700X,
with other work on the machine during the 5-worker run.

`merge.py` was written for this public copy; on our raw files it reproduces
`out/verdicts_t6fix.jsonl` and `out/verdicts_t18full.jsonl` byte for byte. Third-party code and
data credits are in [`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md).
