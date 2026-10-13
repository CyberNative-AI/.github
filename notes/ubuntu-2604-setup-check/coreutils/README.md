# Coreutils on Ubuntu 26.04: code and data

This folder has the code and data behind the [coreutils section](../README.md#coreutils-rust-rewrite-and-measured-command-differences) of the note. In the tested 26.04 container, `ls`, `cp`, `base64` and the other coreutils are uutils 0.10.0 (Rust), not GNU 9.4. We took the coreutils calls that public workflows make directly in `run:` steps and ran each one under both.

| Path | What it is |
|---|---|
| `docker/` | The two arm images: `ubuntu:24.04` and `ubuntu:26.04`, both pinned by digest, plus `python3` and `faketime`. The base images are pinned; the apt-installed packages are not, so check package versions (below) before comparing a rebuild. The 26.04 image also gets `/opt/gnu97`, which holds GNU 9.7 from the 26.04 archive as a third arm. |
| `src/collect.py`, `src/clone.sh`, `src/extract.py` | Sample: anonymous repository search, sparse clones of `.github/workflows`, and coreutils call extraction (parsing only, nothing from a repository runs). |
| `src/make_cases.py`, `src/harness.py`, `src/run_arm.sh` | Each distinct call, run with `shell=False` against a synthetic file set, network off, in each arm. |
| `src/compare.py`, `src/analyze.py` | Compare the arms and apply the decision rule. |
| `src/realinput.py`, `src/adjudicate.py` | Run the call shapes that differ again with realistic inputs, then label each shape. |
| `data/cases-all.jsonl`, `data/cases-confirm.jsonl` | The 7,024 cases (each distinct call in 2 file-set modes, plus 6 positive controls) and the 86 that were run twice more to confirm a difference. |
| `data/invocations-*.jsonl` | 5,133 calls from the random sample (`random-dedup`) and calls from the 175 most-starred repositories (`top`). |
| `results/` | Raw outputs from every arm and pass (`.jsonl.gz`), the real-input runs, plus `RESULT.json`, `ADJUDICATION.json` and `divergent.jsonl`. |

## Check our numbers from the shipped outputs

Python 3 with no extra packages (tested with 3.12), run from this folder:

```sh
gunzip -k results/*.jsonl.gz
python3 src/analyze.py      # writes results/RESULT.json and results/divergent.jsonl
python3 src/adjudicate.py   # writes results/ADJUDICATION.json
```

The `random-dedup` block of `ADJUDICATION.json` has `mechanical_repos: 51`, `hosted_runner_breaking_repos: 0` and `wilson95: [0, 0.00295]`. The Wilson interval is calculated from the assigned labels; it is not a validated upper bound on real hosted-runner workflow failures or on all public repositories.

## Run it again

You need Docker and about 25 minutes of CPU time. No GPU or network is used inside the arms.

```sh
docker build -t coreutils2604:2404 -f docker/Dockerfile.2404 docker
docker build -t coreutils2604:2604 -f docker/Dockerfile.2604 docker
docker run --rm coreutils2604:2604 dpkg-query -W rust-coreutils gnu-coreutils   # 0.10.0-1ubuntu2~26.04.1, 9.7-3ubuntu2.1
docker run --rm coreutils2604:2404 dpkg-query -W coreutils                      # 9.4-3ubuntu6.3
rm -f results/*.jsonl results/*.json
for i in 1 2; do for arm in gnu94 uutils; do src/run_arm.sh $arm data/cases-all.jsonl results/$arm-$i.jsonl; done; done
src/run_arm.sh gnu97 data/cases-all.jsonl results/gnu97-1.jsonl
for arm in gnu94 uutils gnu97; do for i in 1 2; do src/run_arm.sh $arm data/cases-confirm.jsonl results/confirm-$arm-$i.jsonl; done; done
python3 src/analyze.py
for arm in gnu94 uutils gnu97; do
  img=coreutils2604:2604; [ $arm = gnu94 ] && img=coreutils2604:2404
  docker run --rm --network none --user "$(id -u):$(id -g)" --memory 1g --cpus 2 \
    --tmpfs /work:exec,size=64m,uid=$(id -u),gid=$(id -g) -v "$PWD/src:/src:ro" -v "$PWD/results:/out" \
    $img python3 /src/realinput.py $arm /out/real-$arm.jsonl
done
python3 src/adjudicate.py
```

In the shipped passes, 44 GNU 9.4 cases and 42 uutils cases differ materially between passes; their union contains 44 cases. Those are calls whose output is random or depends on the host (`mktemp`, `/proc/sys/kernel/random/uuid`, `uname`, `df`). No confirmed divergent case is among them. `nproc` gives 2 in the uutils arm only because `run_arm.sh` sets `--cpus 2`. Without a CPU limit, all arms print the host's count.

To draw a fresh sample, run `python3 src/collect.py random` (21 days of search pages, about 3 minutes), clone with `src/clone.sh owner/repo`, then run `src/extract.py LIST` (needs PyYAML and shfmt v3.14.1 at `tools/shfmt`) and `src/make_cases.py`. Search results change, so you will get different repositories. We kept one repository per owner with a seeded random choice, and this folder has no script for that step.

## How to read the result

- **The decision rule was fixed before the main run, and it ruled the run invalid.** Its determinism gate needed 99.5% agreement between two passes of the same arm. We got 99.37% for GNU 9.4 and 99.40% for uutils, with 44 cases unstable in at least one arm. Before the final ruling, we made two fixes to the harness: a 1 MiB stdout cap and closing file descriptors between cases (comments `AMENDMENT-01`/`-02` in `src/harness.py`). After the result, only self-reproducing confirmed divergences were counted and added the real-input arm, `realinput.py` and `adjudicate.py`. That step is post hoc, and the code says so.
- **0 of 1,297 comes from per-command labels, not from a test of each call.** `adjudicate.py` gives each command that differed one label, based on what the realistic inputs showed (for example, `base64` decodes real secrets identically), and applies it to every confirmed divergent occurrence of that command. A second run on the same machine, with the same code and images, reproduced every figure and label. That is not an independent replication.
- **Locale.** Every run used `LANG=C.UTF-8`, which is the runner's default. With a real `en_US.UTF-8` locale, uutils differs on `sort`/`ls`/`comm` ordering, `fold -w`, `numfmt --grouping` and `date %c`/`%x`.
- **Additional differences outside the exercised inputs.** `sha256sum -c` accepts a checksum line with leading spaces on GNU 9.4 and 9.7 and rejects it on uutils (exit 1). `timeout -s KILL` exits 137 on GNU and 124 on uutils. No extracted invocation uses timeout -s KILL; real checksum-file contents were not tested.
- **Known extractor defects (they don't change the counts).** `runs-on` matching in `extract.py` is a substring test, so labels such as `ubuntu-latest-32-core` count too. Exact matching gives 1,295 repositories; neither of the two excluded repositories had a confirmed divergence. `env -u VAR` and `env -C DIR` treat the option's argument as the command. None of the 34 `env` calls differs. Fix both before reusing `extract.py`.

## What we changed for publication

- Explicit repository identifiers are replaced by salted HMAC pseudonyms; workflow, job and step locations are removed. Verbatim public workflow arguments can identify a repository by search, so this is pseudonymisation, not anonymisation. The salt and identifier mapping are not published.
- In 381 records of the raw arm outputs, the stdout and stderr text came from the test machine: kernel version, CPU, memory, disks and user IDs (calls such as `uname`, `df`, `id`, `nproc` and reads of `/proc`). That text is replaced with a marker. `out_sha`, `out_len`, `fs_sha` and `rc` are unchanged. The comparison uses those fields, so the analysis gives the same result.
- The image tag in `run_arm.sh` and the first line of `analyze.py` were renamed. Nothing else in `src/` was changed from the code that produced the numbers.

The code is MIT-licensed (`LICENSE`). Published by CyberNative AI LLC. Research, code and writing were done with Anthropic Claude Opus 5.5; the claims and disclosure review used OpenAI gpt-6.1-sol. Tools: Python, Docker, libfaketime and shfmt 3.14.1. Corrections: hello@cybernative.ai. Corrections will be recorded publicly with dates.
