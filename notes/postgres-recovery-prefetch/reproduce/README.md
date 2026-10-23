# recovery_prefetch replay test: reproduction

`gen.sh`, `replay.sh` and `collect.sh` are the scripts that ran inside the containers, unchanged
except for their comment lines. `score.py` is our scorer with one change: it reads the disk from
`DEV` instead of a fixed value. `run.sh` starts them with plain `docker run` and the limits we
used: 2 CPUs, 1 GiB memory, no swap. We started them through our own job scheduler, so
`run.sh` itself is not the launcher that produced `results/`. The scripts run as root with
trust authentication inside a throwaway container; run them only this way, never on a real
server.

You need a folder on the disk you want to test, with about 13 GB free per WAL set
(`full_page_writes` on: 6.0 GB archive, 3.2 GB base backup, 3.2 GB standby copy). Each
uncapped replay takes a few minutes on a hard disk; a capped `try` replay took about
24 minutes on ours.

Images, pinned by digest:

- PostgreSQL 18.6: `postgres@sha256:edb0c08dc33befd0262ab3b5cf1c4f3f8cfd8b09e88c05b45adee29d6761ddb6`
- PostgreSQL 19 RC 1: `postgres@sha256:7c70c2455c1f22cf4fbf90b16345aa4e5f4e3efd68d68f7cd6d014f529a69108`

## Make the WAL, then replay it

```sh
export WORK=/path/on/the/disk/under/test
P18=postgres@sha256:edb0c08dc33befd0262ab3b5cf1c4f3f8cfd8b09e88c05b45adee29d6761ddb6
./run.sh "$P18" gen v18-fon on            # base backup + archived WAL of the UPDATE
./run.sh "$P18" replay v18-fon try 1
./run.sh "$P18" replay v18-fon off 2
./run.sh "$P18" replay v18-fon off 3
./run.sh "$P18" replay v18-fon try 4
```

`gen.sh` writes `gen.json` with the WAL size, LSNs and the table and index sizes in pages.
`replay.sh` copies the base backup, drops the page cache for the copy and the archive, starts
archive recovery with the given `recovery_prefetch`, samples `pg_stat_recovery_prefetch`
every second and stops at "ready to accept connections".

Per-IO read cap, as in our capped runs (use the device that holds `WORK`):

```sh
./run.sh "$P18" replay v18-fon try c1 --device-read-iops /dev/sdX:300
./run.sh "$P18" replay v18-fon off c2 --device-read-iops /dev/sdX:300
```

Each run records the cap it saw in `iomax`.

## Patched and unpatched source builds

`Dockerfile.src` builds PostgreSQL 18.6 twice on top of the 18.6 image: unchanged in
`/opt/pgv` and with the patch in `/opt/pgp`. Put two files next to it first:

- `postgresql-18.6.tar.bz2` from https://ftp.postgresql.org/pub/source/v18.6/
  (sha256 in `postgresql-18.6.tar.bz2.sha256`)
- `v3-0001.patch`: the attachment
  `v3-0001-xlogprefetcher-record-FPW-WILL_INIT-blocks-in-recent.patch` on
  https://www.postgresql.org/message-id/CAE9k0Pkhi-A7A+SOkXbZpMCzP4_q7d3smahwKJHndQYj3n2HHg@mail.gmail.com
  (sha256 `ddef9ab7b50abc6d1ea55bb2ebb33643c1f7e82a7e15384bc9d86f0f40344de3`)

```sh
docker build -f Dockerfile.src -t pg186src .
PP=(-e PATH=/opt/pgp/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin)
PV=(-e PATH=/opt/pgv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin)
./run.sh pg186src replay v18-fon try pv1 "${PV[@]}"
./run.sh pg186src replay v18-fon try pp2 "${PP[@]}"
./run.sh pg186src replay v18-fon try cp5 "${PP[@]}" --device-read-iops /dev/sdX:300
```

Each run records the `postgres` binary it used in `binary`.

## Score

```sh
./run.sh "$P18" collect ./results-new
DEV=8:32 python3 score.py results-new > score-new.json   # DEV = major:minor of the disk
python3 score.py results > score.json                     # recomputes our numbers
```

`score.py` reads each run's "redo done" log line, the container's IO counters for the disk
(`io0` before, `io1` after) and the final `pg_stat_recovery_prefetch` row, applies the validity
checks (redo logged, ready, at least 90% of the WAL size read from disk, setting took effect)
and gives the ratio of median `try` to median `off` redo time per cell. Run names: a number is
the uncapped Debian image; `c` capped; `pv` and `pp` the unchanged and patched source builds;
`cp` patched and capped.

`results/` holds our 22 runs from October 23: `v18-fon` and `v18-foff` (PostgreSQL 18.6,
`full_page_writes` on and off) and `v19-fon` (19 RC 1). Each run folder has the server log
(`pg.log`), IO counters, per-second prefetch samples (`prefetch.csv`: time, replay LSN,
prefetch, hit, skip_init, skip_new, skip_fpw, skip_rep, wal_distance, block_distance,
io_depth), the final counters and the cap. `score.json` is the scorer's output for it.
`operator-search.json` is the October 23 GitHub code search for `recovery_prefetch` in
operator and HA tool repositories.
