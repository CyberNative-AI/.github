# Reproduce

Synthetic inputs only: no package or image from the compromised release is downloaded.

```sh
python3 make_inputs.py WORKDIR/inputs        # T=1.107.0, M=1.82.7, C=1.89.3, N=1.106.2
docker build -t local/pip-audit:2.10.1 -f pip-audit.Dockerfile .
bash run_scanners.sh WORKDIR 1               # raw output in WORKDIR/out/rep1
python3 score.py WORKDIR/out/rep1 > score.json
```

Forms: F1 `requirements.txt`, F2 `uv.lock`, F3 `poetry.lock`, F4 an installed
`litellm-V.dist-info` folder under `usr/local/lib/python3.12/site-packages`.

`raw-rep1.tar.gz` and `raw-rep2.tar.gz` hold our two runs of October 22 (finished 08:02:46Z
and 08:08:49Z): each scanner's JSON, stderr and exit code per cell, plus the scanner and
database versions (`ver-*`). `score-rep1.json` and `score-rep2.json` are `score.py` run on
them; the outcomes and exit codes are the same in both runs.

```sh
mkdir raw && tar -xzf raw-rep1.tar.gz -C raw && python3 score.py raw/rep1 | cmp - score-rep1.json
```

The raw output contains advisory data from GitHub, PyPA, OpenSSF, NVD and FIRST under their own
terms: see [`THIRD-PARTY-DATA.md`](THIRD-PARTY-DATA.md).

Scanner databases change daily, so a run today will differ from ours where a database has
been updated.
