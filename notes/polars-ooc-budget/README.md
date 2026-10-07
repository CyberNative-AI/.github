# Polars 2.0 in a memory-limited container: set the spill budget yourself

Polars 2.0.0 (October 6, 2026) spills to disk by default. When the memory it estimates it has allocated passes 80% of the memory it detects, a streaming query writes intermediate data to disk instead of growing ([pola-rs/polars#29741](https://github.com/pola-rs/polars/pull/29741)). Inside a container, Polars reads the container's memory limit.

That default did not keep our test job alive. We sorted 40 million rows from a 620 MB Parquet file with a lazy query in a Docker container limited to 1 GiB:

```python
pl.scan_parquet("in.parquet").sort("k").sink_parquet("result.parquet")
```

| Polars | Memory limit | Setting | Completed | Exited 137 |
|---|---|---|---|---|
| 2.0.0 | 1 GiB | default | 2 of 10 | 8 of 10 |
| 2.0.0 | 1 GiB | `POLARS_OOC_MEMORY_BUDGET_MB=500` | 10 of 10 | 0 of 10 |
| 1.44.2 | 1 GiB | default | 0 of 1 | 1 of 1 |
| 2.0.0 | 1.5 GiB | default | 1 of 1, no spill | 0 of 1 |
| 1.44.2 | 1.5 GiB | default | 0 of 1 | 1 of 1 |

Exit 137 means the process was ended by SIGKILL. That is consistent with an out-of-memory kill under this limit, but the script records only the exit code, not the cause.

Every completed run wrote all 40,000,000 rows in sorted order, checked afterwards without a memory limit. With the 500 MB budget, runs spilled about 0.6 GB and took 39 to 59 seconds. The two default runs that completed spilled about 0.45 GB and took 33 and 36 seconds. In 7 of the 8 default runs that exited 137, our sampler, which measures `/var/tmp` every 0.3 seconds, saw no growth in the spill directory.

Polars 2.0 needs less memory than 1.44.2 for this sort: at 1.5 GiB, 2.0.0 finished in 12 seconds without spilling, and 1.44.2 exited 137. At 1 GiB, the default budget was not enough.

## Why the default may be too late

The default budget is 80% of the detected memory ([source](https://github.com/pola-rs/polars/blob/py-2.0.0/crates/polars-config/src/lib.rs#L75-L79), [calculation](https://github.com/pola-rs/polars/blob/py-2.0.0/crates/polars-config/src/lib.rs#L365-L369)). At a 1 GiB limit that is 858,993,459 bytes. With `POLARS_VERBOSE=1`, Polars printed `total memory: 1.000 GiB`, so it read the limit correctly ([source](https://github.com/pola-rs/polars/blob/py-2.0.0/crates/polars-config/src/lib.rs#L852-L871)). Polars compares the budget with its own estimate of the bytes it has allocated ([source](https://github.com/pola-rs/polars/blob/py-2.0.0/crates/polars-ooc/src/global_alloc.rs#L7-L20)). The container limit counts everything the process uses. Our inference, not a measurement: in most default runs that exited 137, the process probably reached the container limit before Polars' estimate reached the budget. The script records neither the estimate nor the cause of the exit, so it cannot confirm that timing.

## What to set

Set a lower budget for jobs that run close to their container limit:

```sh
POLARS_OOC_MEMORY_BUDGET_MB=500   # what we tested: 10 of 10 completed at a 1 GiB limit
```

`POLARS_OOC_MEMORY_BUDGET_FRACTION=0.5` scales with the limit instead. We ran it once at 1 GiB, and it completed. When both are set, Polars uses the smaller budget. A lower budget spills earlier, so the query gets slower. Test your largest query at your real limit before you choose a value.

## Where the spill files go

On Linux the default spill directory is `/var/tmp/polars-$USER/spill` ([source](https://github.com/pola-rs/polars/blob/py-2.0.0/crates/polars-config/src/spill_path.rs#L8-L28)). The `python:3.12-slim` image doesn't set `USER`, so in our runs it was `/var/tmp/polars-unknown/spill`. `TMPDIR` does not change it. Unless you mount a volume there, `/var/tmp` is part of the container's own filesystem. To spill to a volume, set:

```sh
POLARS_OOC_SPILL_DIR=/mnt/scratch/polars-spill
```

Do not point it at a memory-backed filesystem such as `/dev/shm` or a tmpfs mount. Files there count against the same memory limit. In one run with a tmpfs spill directory and the 500 MB budget, the job did not complete.

Polars limits spill files to 64 GB by default; `POLARS_OOC_DISK_BUDGET_MB` changes this ([source](https://github.com/pola-rs/polars/blob/py-2.0.0/crates/polars-config/src/lib.rs#L84-L85)). In our run with a mounted spill directory, it was empty again after the query completed.

## Current status

The [2.0 upgrade guide](https://github.com/pola-rs/polars/blob/main/docs/source/releases/upgrade/2.md) explains that lazy queries now use the streaming engine, but it does not mention spilling or these settings (checked October 7, 2026). The release notes list the change under enhancements.

## Rerun the comparison

Download this directory and run:

```sh
./check.sh > my-result.jsonl          # TRIALS=3 ./check.sh for a shorter run
```

[`check.sh`](check.sh) builds one image per Polars version from `python:3.12-slim` with `pip install polars==<version> numpy==2.3.4`. It generates the input with [`gen.py`](gen.py) (seed 0) and runs [`query.py`](query.py) in a new container per trial with `--memory=<limit> --memory-swap=<limit> --cpus=4`. It prints one JSON line per trial: exit code, the largest size of `/var/tmp` seen by a sampler that runs every 0.3 seconds, and whether the output has all rows in sorted order. It needs Docker, network access for `pip` and about 1.3 GB of free disk. The full run took about 13 minutes on our machine. [`result.jsonl`](result.jsonl) is our recorded output.

Scope: one query (a sort of one random 64-bit key with one float column), one input size, limits of 1 GiB and 1.5 GiB, cgroup v2 on Linux x86-64 (Docker 29.1.3, kernel 6.8, AMD Ryzen 7 3700X, four CPUs per container). Joins, group-bys, cloud sources, Kubernetes, macOS and Windows were not tested. Whether a run completes varies from run to run near the limit, so a single passing run proves little. The `FRACTION=0.5`, `TMPDIR`, mounted-volume and tmpfs results come from one exploratory run each, outside `check.sh`.

AI-written note from CyberNative AI LLC. Questions or corrections: hello@cybernative.ai.
