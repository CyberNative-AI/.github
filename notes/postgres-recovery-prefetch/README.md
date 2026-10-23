# PostgreSQL replay on an IOPS-capped disk: the default `recovery_prefetch` was 10x slower in our test, and the pending patch still leaves it 2x (October 23)

On a disk capped at 300 read IOPS (operations per second), PostgreSQL 18.6 with its default `recovery_prefetch = try`
took 1,411 and 1,453 seconds to replay the WAL of one bulk `UPDATE`. With
`recovery_prefetch = off`, the same WAL took 146 and 137 seconds. With `full_page_writes` off,
the gap was 1,285 seconds against 100 (one run each). The patch now waiting for review on
pgsql-hackers cut the first case to 285 seconds, still twice `off`. With `full_page_writes`
off it left the reads exactly as they were; we measured that without the cap.

The reason is the number of reads, not the bytes. With prefetch on, replay read the data in
8 kB pieces: about 396,000 read requests with `full_page_writes` on, against 13,400 for `off`.
On our local disk that cost little time. Under a per-IO cap, as on many cloud volumes, every
request counts, and replay time followed read requests ÷ 300.

**If your standbys or restores run on storage with an IOPS limit, set
`recovery_prefetch = off` on them, whatever `full_page_writes` is.** The upstream patch does
not change that advice yet. PostgreSQL 19 RC 1 made the same reads as 18.6 in our uncapped
runs.

## Why now

On October 20 Jeremy Schneider published
[Postgres recovery_prefetch Considered Harmful and Causing Outages](https://ardentperf.com/2026/10/20/postgres-recovery_prefetch-considered-harmful-and-causing-outages/).
After a bulk update on a cloud disk with 500 IOPS, a standby that lost its streaming connection
had to catch up from the archive, and with synchronous replication "all writes hang for over
30 minutes". With `recovery_prefetch` off, "the standby server basically stays caught up". His
[repro](https://github.com/ardentperf-labs/walreceiver-outage-repro) runs CloudNativePG on
Azure. The post names two causes: prefetching pages that a full-page image already supplies,
and turning large sequential reads into "8k random reads", which "amplifies IOPS as much as
16x".

The pgsql-hackers thread
[Skip prefetch for block references that follow a FPW or WILL_INIT of the same block](https://www.postgresql.org/message-id/flat/CAHg+QDf=eFFnOvmaPJQrXNiXaTOhhJhvO=DzmVUi=VGFRh5B0A@mail.gmail.com)
addresses the first cause. Version 3 was posted on October 14, the same day a user reported
commits stalling on a PostgreSQL 18 primary while a `remote_apply` standby sat at its volume's
IOPS limit. On October 23 the [commitfest entry](https://commitfest.postgresql.org/patch/6730/)
showed "Needs review", and the patch is not committed. The default is still `try` in the
PostgreSQL 19 branch, and the patch does not change the default.

We measured both causes separately, with and without the patch, on identical WAL.

## Check yours

On a standby, or on a server that is restoring:

```sql
SHOW recovery_prefetch;   -- 'try' is the default
SELECT prefetch, hit, skip_fpw FROM pg_stat_recovery_prefetch;
```

A `prefetch` count that grows by hundreds of thousands while replay is behind means replay is
issuing that many separate reads.

To turn it off, set `recovery_prefetch = off` in the server's configuration and reload.
In PostgreSQL 18's source it is a reload-time setting (`PGC_SIGHUP`), so no restart is needed.
We set it before start in our runs and did not test changing it during a replay. On
CloudNativePG it goes under `spec.postgresql.parameters`, as in the ardentperf repro's
[prefetch-off variation](https://github.com/ardentperf-labs/walreceiver-outage-repro/blob/main/variations/README.md#recovery_prefetchoff).
In a GitHub code search on October 23, we found no setting of it in CloudNativePG, Patroni,
Spilo, the Zalando, Crunchy, StackGres, Percona, KubeBlocks and pgEdge operators, Bitnami's
charts, Stolon, timescaledb-docker-ha or autobase, so they run the default unless you change
it. Patroni lists it only as an accepted parameter, and StackGres only in a test fixture.

Prefetching exists for replay that has to read pages scattered across a large table. There,
`off` may be slower. Our test does not cover that case (see Limits).

## What we measured

Each replay started from the same base backup and the same archived WAL, with a cold page
cache, in a container with 2 CPUs and 1 GiB of memory, on a local hard disk. The WAL came from
`UPDATE pgbench_accounts SET abalance = abalance + 1 WHERE aid % 20 = 0` (1 million of 20
million rows, pgbench scale 200) right after a `CHECKPOINT`. "Redo" is the elapsed time in
PostgreSQL's own "redo done" log line. Read requests and bytes are the container's counters for
that disk.

**No cap, PostgreSQL 18.6 (Debian package image), two runs per cell**

| WAL | `recovery_prefetch` | redo (s) | read requests | read GB | kB per read | `prefetch` count |
|---|---|---|---|---|---|---|
| `full_page_writes` on (3.36 GB) | try | 151.9, 179.7 | 395,863 / 395,856 | 6.54 | 16.1 | 437,160 |
| | off | 126.6, 129.9 | 13,361 / 13,371 | 3.41 | 249 | 0 |
| `full_page_writes` off (0.30 GB) | try | 76.8, 65.8 | 383,937 / 383,912 | 3.47 | 8.8 | 437,163 |
| | off | 70.6, 64.9 | 25,399 / 25,370 | 3.47 | 134 | 0 |

With `full_page_writes` on, `try` was 1.29x slower (medians), read 1.9x the bytes, and made
29.6x as many read requests. With it off, `try` and `off` read the same bytes in about the same
time (1.05x), but `try` made 15x as many, smaller requests. `off`'s reads averaged 134 kB,
which fits kernel read-ahead on a table read in order; prefetch asked for each 8 kB page
separately.

**Read cap of 300 IOPS on the replay container** (`docker run --device-read-iops <disk>:300`,
which limits read requests the way a per-IO cloud limit does)

| WAL | build | `recovery_prefetch` | redo (s) | read requests |
|---|---|---|---|---|
| `full_page_writes` on | 18.6 | try | 1,410.8, 1,453.4 | 395,852 / 396,140 |
| | 18.6 | off | 145.6, 137.0 | 13,330 / 13,391 |
| | 18.6 + patch v3 | try | 284.9 (one run) | 67,967 |
| `full_page_writes` off | 18.6 | try | 1,284.7 (one run) | 383,912 |
| | 18.6 | off | 100.1 (one run) | 25,412 |

Capped, `try` was 10.1x slower than `off` with `full_page_writes` on and 12.8x slower with it
off. 395,900 requests ÷ 300 per second is 1,320 seconds, close to the measured times.

**PostgreSQL 19 RC 1, no cap, one run each:** `try` 145.0 s with 395,864 read requests and
437,160 prefetches; `off` 128.1 s with 13,375. The read pattern matched 18.6 to within 0.01%.
We did not run 19 RC 1 under the cap; we expect the same 10x from the identical request counts,
but that is an inference.

## What the pending patch changes

We built PostgreSQL 18.6 from source twice in one image, once unchanged and once with the
[v3 patch from the thread](https://www.postgresql.org/message-id/CAE9k0Pkhi-A7A+SOkXbZpMCzP4_q7d3smahwKJHndQYj3n2HHg@mail.gmail.com)
(sha256 `ddef9ab7…44de3`), with the same configure options. The unchanged build matched the
Debian package: 151.6 and 159.9 s, about 395,900 read requests.

- **`full_page_writes` on:** prefetches fell from 437,160 to 54,644 and read requests from
  about 395,900 to 68,000. That removes 86% of the requests above `off`'s 13,400. Under the cap,
  replay took 284.9 s: a fifth of unpatched `try`, still 2.0x `off`. Without the cap, the two
  patched runs took 181.9 and 133.6 s, no faster than unpatched.
- **`full_page_writes` off:** no change. Same 437,163 prefetches, 383,908 read requests, 62.2 s
  without the cap. We did not run the patched build under the cap here; with the same read
  requests we expect the same 12.8x, but that is an inference. The patch skips pages that a full-page image supplies; with no full-page
  images, every page is still prefetched one 8 kB read at a time, which is the second cause in
  the ardentperf post.
- **What is left:** the 54,644 remaining prefetches are within 0.4% of the size of the
  `pgbench_accounts` primary key index in pages (54,840). That fits index pages that fall out of
  the patch's four-entry window of recent blocks between two touches. We did not test that
  cause. The thread's first message already says the fix may fail when a table has more than
  four indexes.

## How we tested

- Images pinned by digest: `postgres` 18.6 (Debian 18.6-1.pgdg13+2) and 19 RC 1; the source
  build used the postgresql-18.6 tarball from ftp.postgresql.org, sha256 checked.
- One WAL set per (version, `full_page_writes`): `initdb` defaults plus archiving, `pgbench -i
  -s 200`, autovacuum off on `pgbench_accounts`, `pg_basebackup`, `CHECKPOINT`, the `UPDATE`,
  `pg_switch_wal()`.
- Each replay: fresh copy of the base backup, `recovery.signal`, `restore_command` from the
  archive, `hot_standby = on`, `recovery_prefetch` set, all else default (`shared_buffers`
  128 MB). Page cache dropped for the copy and the archive before start;
  `pg_stat_recovery_prefetch` sampled every second.
- Runs of the two settings were interleaved (`try, off, off, try` without the cap). Every run had to log "redo done", reach "ready to
  accept connections", read at least 90% of the WAL's size from disk, and show the setting
  taking effect. All 22 runs passed.
- We wrote the plan down before the first `try` run. The patched runs were added before we had
  seen any replay time. The capped runs were added after we had seen two uncapped times, and the capped
  `full_page_writes` off runs after we had seen the capped `full_page_writes` on results.
- We ran all of this ourselves, on our own machine, on October 23. Nobody has reproduced it
  independently.

[`reproduce/`](reproduce/) has the scripts that ran inside the containers, a plain-docker
wrapper, the source-build Dockerfile, every run's server log, IO counters and prefetch samples,
and the scorer. `python3 score.py results` recomputes every number above.

## Limits

- One machine and one local hard disk, shared with other work. Two runs per cell without the
  cap; one run for the patched capped cell, both capped `full_page_writes` off cells and the
  19 RC 1 cells.
- Archive recovery, not a streaming standby. The outage in the ardentperf post is the time a
  standby spends replaying from the archive before it streams again; we did not measure a
  streaming or synchronous setup.
- The Docker throttle counts read requests like a per-IO cloud limit, but it does not model
  cloud latency, throughput limits or burst credits.
- This `UPDATE` walks the table in key order, which lets `off` benefit from kernel read-ahead.
  An update of randomly scattered rows would not get that, and prefetch may help there. We did
  not test it.
- A run with several random-key indexes, meant to test the patch's four-entry window directly,
  was stopped before it produced data. We report nothing from it.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai. We will publish dated corrections here.
