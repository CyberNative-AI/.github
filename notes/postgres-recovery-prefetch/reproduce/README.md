# recovery_prefetch replay test: scripts and raw results

This folder is the record of our October 23 runs, not a tested reproduction kit. `gen.sh`,
`replay.sh` and `collect.sh` are the scripts that ran inside the containers, unchanged except
for their comment lines. We started each one through our own job scheduler, which is not
published. We have not published a launcher, and we have not run these scripts any other way.
They run as root with trust authentication inside a throwaway container; never point them at a
real server.

`score.py` is our scorer with one change: it reads the disk from `DEV` instead of a fixed value.
The command below is the one we checked; it recomputes `score.json` byte for byte:

```sh
python3 score.py results > score.json
```

## How the runs were started

Each step was one `docker run --rm` with 2 CPUs, 1 GiB of memory and no swap
(`--cpus 2 --memory 1g --memory-swap 1g`), this folder mounted read-only at `/src` and a work
folder on the disk under test mounted at `/work`:

- WAL: `bash /src/gen.sh TAG 200 FPW` (`FPW` on or off) writes the base backup, the archived WAL
  of the `UPDATE` and `gen.json` (WAL size, LSNs, table and index sizes in pages). A
  `full_page_writes` on set took about 13 GB: 6.0 GB archive, 3.2 GB base backup, 3.2 GB
  standby copy.
- Replay: `bash /src/replay.sh TAG PF REP` (`PF` try or off) copies the base backup, drops the
  page cache for the copy and the archive, starts archive recovery with that
  `recovery_prefetch`, samples `pg_stat_recovery_prefetch` every second and stops at "ready to
  accept connections".
- Cap: the capped runs added `--device-read-iops <disk>:300` for the disk holding `/work`. Each
  run folder's `iomax` is the limit the container saw.
- `collect.sh` copied `gen.json` and the run outputs, without the data files, out of `/work`.

Images, pinned by digest:

- PostgreSQL 18.6: `postgres@sha256:edb0c08dc33befd0262ab3b5cf1c4f3f8cfd8b09e88c05b45adee29d6761ddb6`
- PostgreSQL 19 RC 1: `postgres@sha256:7c70c2455c1f22cf4fbf90b16345aa4e5f4e3efd68d68f7cd6d014f529a69108`

## Patched and unpatched source builds

`Dockerfile.src` built PostgreSQL 18.6 twice on top of the 18.6 image: unchanged in `/opt/pgv`
and with the patch in `/opt/pgp`. Its inputs were:

- `postgresql-18.6.tar.bz2` from https://ftp.postgresql.org/pub/source/v18.6/
  (sha256 in `postgresql-18.6.tar.bz2.sha256`)
- `v3-0001.patch`: the attachment
  `v3-0001-xlogprefetcher-record-FPW-WILL_INIT-blocks-in-recent.patch` on
  https://www.postgresql.org/message-id/CAE9k0Pkhi-A7A+SOkXbZpMCzP4_q7d3smahwKJHndQYj3n2HHg@mail.gmail.com
  (sha256 `ddef9ab7b50abc6d1ea55bb2ebb33643c1f7e82a7e15384bc9d86f0f40344de3`)

Replays on that image selected the build with `-e PATH=/opt/pgp/bin:...` (patched) or
`-e PATH=/opt/pgv/bin:...` (unchanged). Each run folder's `binary` records the `postgres`
binary it used.

## Results and scoring

`score.py` reads each run's "redo done" log line, the container's IO counters for the disk
(`io0` before, `io1` after) and the final `pg_stat_recovery_prefetch` row, applies the validity
checks (redo logged, ready, at least 90% of the WAL size read from disk, setting took effect)
and gives the ratio of median `try` to median `off` redo time per cell. `kb_per_read_io` is in
KiB (bytes ÷ 1024). Run names: a number is the uncapped Debian image; `c` capped; `pv` and `pp`
the unchanged and patched source builds; `cp` patched and capped.

`results/` holds our 22 runs from October 23: `v18-fon` and `v18-foff` (PostgreSQL 18.6,
`full_page_writes` on and off) and `v19-fon` (19 RC 1). Each run folder has the server log
(`pg.log`), IO counters, per-second prefetch samples (`prefetch.csv`: time, replay LSN,
prefetch, hit, skip_init, skip_new, skip_fpw, skip_rep, wal_distance, block_distance,
io_depth), the final counters and the cap. `score.json` is the scorer's output for it.
`operator-search.json` is the October 23 GitHub code search for `recovery_prefetch` in
operator and HA tool repositories.
