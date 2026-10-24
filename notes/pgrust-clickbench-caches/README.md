# pgrust 0.4-beta's caches on ClickBench's queries: the submitted defaults gave an 8-18% lower hot geomean than `granule` mode in our test, and the part that repeated was the dictionary cache on three LIKE queries (October 24)

We ran the released pgrust 0.4-beta x86_64 binary with the settings from its ClickBench
pull request ([ClickHouse/ClickBench#2751](https://github.com/ClickHouse/ClickBench/pull/2751))
and the benchmark's 43 queries on 16 million rows, once in each cache mode. With the submitted
default, `pgrust.condition_cache=full`, the hot-run geomean was 8% lower in one fresh load and
18% lower in another than with `granule`, the mode the pull request describes as "what
ClickHouse's query condition cache keeps".

The part of that gain that repeated in every load came from three queries, Q20 to Q22, which
filter on `URL LIKE '%google%'` or `Title LIKE '%Google%'`. With the defaults, Q20 took
1.2-1.3 ms on a hot run in loads A and B; in `granule` mode it took 30-32 ms. Those three
queries alone lowered the 43-query geomean by about 9% in each of our three loads. Turning off
only `pgrust.dict_filter_cache` brought them back to 28-58 ms. So the gain is the dictionary
filter cache, which in the pull request's words keeps "which strings in each part's dictionary
matched" a text filter, not the reuse of stored match counts.

**If you compare pgrust 0.4-beta's hot numbers on ClickBench: in our test the submitted
defaults gave a hot geomean 8-18% lower than `pgrust.condition_cache=granule` (which does not
use the dictionary cache), and 8% lower than the same defaults with only
`pgrust.dict_filter_cache=off` (load C). The part that repeated across loads, about 9%, is three LIKE
queries.** Whether ClickBench's caching rules allow that cache is for its maintainers to
decide. We take no position on it, and none on the earlier v0.4-preview build, which we could
not run.

Also measured, on the same runs:

- **Count reuse: one query.** The pull request says "A repeated count-only query can be
  answered from those counts." That happened on one benchmark query, Q1
  (`COUNT(*) WHERE AdvEngineID <> 0`): a warm repeat read 0 granules in `full` mode against
  1,476 in `granule` mode, and was 1-2 ms faster.
- **No wrong or stale answers.** With tie-breakers added to `ORDER BY`, all four modes returned
  the same rows for every query in both loads. After INSERTs and DELETEs on a warm server,
  every mode returned the new counts.
- **EXPLAIN does not account for count reuse.** For Q1 in `full` mode, the `Granules:` line
  leaves 1,476 granules in none of its fields (details below).
- **None of the listed markers in the beta binary.** `strings` on its `postgres` finds none of
  the markers that [ClickHouse/ClickBench#2165](https://github.com/ClickHouse/ClickBench/pull/2165)
  listed against v0.4-preview.

## Why now

ClickBench removed pgrust on September 22
([ClickHouse/ClickBench#2165](https://github.com/ClickHouse/ClickBench/pull/2165)), citing
per-query kernels and result caching in the v0.4-preview build. On October 22 pgrust's author
opened #2751 to add v0.4-beta, listing each cache with its setting and default and inviting
reviewers to "rerun with whatever settings you think fit best". On October 23
[the author wrote on Hacker News](https://news.ycombinator.com/item?id=50209450) that the
earlier hot-run cache held "which predicates match which strings in our dictionaries", the
kind of intermediate data ClickBench allows. ClickBench's README says "Query result caches
should be disabled". We found no measurement of what each of the new caches is worth.

## Results

Hot geomean in each mode divided by `granule` mode's (below 1.000 = faster). The geomean is over
the 43 queries of the hot time plus 10 ms, ClickBench's constant; the hot time is the faster of
runs 2 and 3 after a server restart. Loads A and B are two fresh loads of the same data; load C
is the diagnostic run we added after seeing load A.

| Mode | Load A | Load B | Load C |
|---|---|---|---|
| `full` (submitted default) | 0.917 | 0.825 | 0.865 |
| `rows` | 0.878 | 0.831 | not run |
| `off` | 1.028 | 0.957 | not run |
| `full`, `dict_filter_cache=off` | not run | not run | 0.942 |
| `rows`, `dict_filter_cache=off` | not run | not run | 0.980 |
| `granule` | 1.000 | 1.000 | 1.000 |

Hot times of the three LIKE queries, in milliseconds:

| Query | `full` A | `granule` A | `full` B | `granule` B | `full` C | `full`, dict off, C | `granule` C |
|---|---|---|---|---|---|---|---|
| Q20 `SELECT COUNT(*) ... WHERE URL LIKE '%google%'` | 1.34 | 30.22 | 1.25 | 32.32 | 1.16 | 28.44 | 47.41 |
| Q21 `... WHERE URL LIKE '%google%' AND SearchPhrase <> '' GROUP BY SearchPhrase` | 2.55 | 29.70 | 2.27 | 32.44 | 2.44 | 32.30 | 37.96 |
| Q22 `... WHERE Title LIKE '%Google%' AND URL NOT LIKE '%.google.%' ...` | 8.95 | 68.74 | 12.23 | 80.82 | 11.64 | 57.80 | 56.45 |

Query numbers count from 0, as in ClickBench's result files; Q20 is the 21st line of
`queries.sql`.

Putting only Q20-Q22's `full` times in place of their `granule` times gives a ratio of 0.915,
0.912 and 0.909 in loads A, B and C. Without Q20-Q22, `full`/`granule` was 1.003, 0.898 and
0.948: the other 40 queries did not show a consistent effect across all three loads. Two modes that should differ
little moved about as far: `off`/`granule` was 1.028 in load A and 0.957 in load B. We read the
rest as run-to-run variation on this machine, not as a cache effect, but a smaller cache
effect could be hidden in it.

Cold runs (run 1 after a restart) were slower in `full` mode in two of the three loads:
geomean `full`/`granule` 1.31 (A), 1.08 (B) and 0.99 (C). ClickBench's published score combines
cold and hot runs; we did not compute that combination.

## Count reuse: one query

Q1 is `SELECT COUNT(*) FROM hits WHERE AdvEngineID <> 0`. Its warm EXPLAIN, in both loads:

```
full:     Granules: 0 read, 492 skipped, 0 answered; 0 part opens
granule:  Granules: 1476 read, 492 skipped, 0 answered; 0 part opens
```

Hot time 1.30 ms against 2.08 ms in load A, 1.04 against 3.06 in load B. No other query read 0
granules in `full` mode while reading some in `granule` mode. Q1 alone moves the 43-query
geomean by 0.2% (load A) and 0.4% (load B).

## EXPLAIN does not account for count reuse

In the Q1 readouts above, `granule` mode accounts for 1,968 granules (1,476 read, 492 skipped).
In `full` mode, 492 are skipped and the other 1,476 appear in no printed field. "answered" was 0
on all 688 `Granules:` lines in the 860 EXPLAINs we ran.

At the v0.4-beta tag (`38634b4`), the `Granules:` line prints three counters: granules decoded,
skipped on a `NoneMatch` verdict, and answered from statistics. The engine keeps five;
`report_driven` in `crates/gravity/exec/src/admit/entry/instrument.rs` copies the first three
into the EXPLAIN report (line 420: `r.granules = [ran.granules[0], ran.granules[1], ran.granules[2]];`).
The fourth counts parts answered whole from part-grain statistics, the fifth granules decoded
selectively. Separately, the condition cache's whole-part path (`whole_part_hit` in
`crates/gravity/hosts/src/ops/scan/pgrc/granule_source.rs`) counts into its own counters,
condition-cache hits and `COND_PARTS`, which are not in the EXPLAIN report either.

We did not trace which path handled Q1's 1,476 granules, so we do not say which counter holds
them. What the readouts show is that a reviewer checking a ClickBench run for count reuse cannot
see it in EXPLAIN, only infer it from granules missing from the total.

## Correctness

- **Answers across modes.** We ran every query again with its select-list positions appended to
  `ORDER BY` as tie-breakers, so that a legal difference between tied rows under `LIMIT` cannot
  look like a wrong answer. The result hashes of `full`, `rows` and `granule` matched `off` for
  all 43 queries in both loads. In the plain runs, six queries (Q17, Q21, Q22, Q24, Q38, Q39)
  returned different rows in different modes, Q17 and Q24 also between runs of one mode. Each
  has a `LIMIT` over rows whose order the query leaves open (no `ORDER BY`, or equal sort keys);
  with tie-breakers, all modes agreed.
- **Staleness.** For each mode we ran Q1 and Q20 three times on a fresh server to fill the
  caches, then either inserted rows (1,000 with `AdvEngineID <> 0` and 50 matching
  `'%google%'`) or deleted rows, ran both again on the same server, and compared the counts
  with a recount after a restart with all three caches off. That is 16 checks per load (4 modes,
  insert and delete, 2 queries). Every mutation changed the counts, and every warm count matched
  the recount.
- No query returned an error in any mode.

## Static check of the beta binary

`strings` on `bin/postgres` from the v0.4-beta x86_64 tarball (sha256 `319f9364...` for the
binary) finds 0 occurrences of each of: `clickbench`; the v0.4-preview refusal messages quoted
in #2165 (`phrase-min`, `t3 distinct`); `irprobe`; `PGRUST_GRAVITY_Q`; `windowreplay`;
`metaanswer`; `HOST_EXTRACT`; the benchmark's literal constants `435090932899640449`,
`3594120000172545465` and `2868770270353813622`; the column names `AdvEngineID`,
`SearchPhrase` and `CounterID`. This shows these markers are absent from this build. It does not
show the absence of other specialization.

## How we measured

- **Binary:** `pgrust-0.4-beta-linux-x86_64.tar.gz` from pgrust.com, sha256
  `9a53fdc039ca338808702641369b0ac7d6c163124f76f2bfd21860b0be9fb7bb`, which matches its
  published `.sha256` file. This is the generic x86_64 build, the one the pull request's
  `select-build` script picks on this CPU. v0.4-preview was published only as an aarch64
  Neoverse-V2 build, so we could not run it.
- **Settings:** the block from #2751's `install` script at its head commit `deabb4a5`, with
  memory and thread counts set to the container's limits (6 threads, 12 GiB) instead of the
  host's. Between modes only `pgrust.condition_cache` changes; `dict_filter_cache` and
  `zone_store` stay on, as submitted. In load C, two modes also set `dict_filter_cache=off`.
- **Data:** `hits_0` to `hits_15` of ClickBench's partitioned `hits` files, 16,000,000 rows
  (16 of 100 partitions), loaded with one `COPY ... (FORMAT 'parquet', COERCE_EPOCH true)` per
  file, then `ANALYZE`. The pull request loads the single 100M-row file the same way.
- **Loop:** for each mode and each of the 43 queries from #2751's `queries.sql`, restart the
  server, run the query three times through `psql` with `\timing`, then run one
  `EXPLAIN (ANALYZE, VERBOSE)` on the same warm server. This is our own loop, not ClickBench's
  `benchmark.sh` driver.
- **Machine:** a desktop AMD Zen 2 CPU (8 cores), in a Docker container limited to 6 CPUs and
  16 GiB with no network, Debian 13 slim. The data fits in memory, so every run, cold or hot,
  read from a warm page cache.
- **Order of work:** we wrote down the method and the decision rule before the main runs.
  Load C, with `dict_filter_cache` off, was added after load A's results to find which cache
  made the difference, and is reported as a description, not a verdict. Before running we
  expected the stored counts to account for most of any gain; they accounted for one query.

## Limitations

- One machine, 16% of the benchmark's rows, the generic build. A dictionary cache saves work
  that grows with the number of rows, so the full 100M rows would probably show a larger
  effect. We did not measure it.
- We ran this once on our own machine; nobody else has reproduced it.
- Outside Q20-Q22, hot times moved by about 5-10% between loads, which hides any small effect.
- No concurrent-query test.

## Files

[`reproduce/`](reproduce/) holds the scripts that ran inside the containers, the raw timing,
answer-hash and staleness records of every run, every EXPLAIN output, the scorer (which
recomputes `score.json` byte for byte) and a second, independent recount. See
[`reproduce/README.md`](reproduce/README.md).

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai. We will publish dated corrections here.
