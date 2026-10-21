# Patroni and PostgreSQL 19 lock capacity: reproduction

Each server runs in its own throwaway container, started by `run.sh`: no network, data in tmpfs, 2 CPUs, 6 GiB memory with no swap, 1024 processes, a 20-minute deadline (`DEADLINE=` in seconds to change it), this folder read-only and a new `./out/NAME` as the only writable path. The scripts run as root with trust authentication, so run them only this way, never on a host or a real cluster. The container is removed when the script ends, times out or you press Ctrl-C. CPU only; each run takes under a minute.

Images, pinned by digest:

- PostgreSQL 18.6: `postgres@sha256:74935e72241653ca55e0414067e6d8763aceb8a810eb51b452253ec3dcfc4336` (`postgres:18.6-trixie`)
- PostgreSQL 19rc1: `postgres@sha256:9df2c846b8b9130f3877a30495d9931538954768602a64d32c415c44bd958e9c` (`postgres:19rc1-trixie`)

## Build the Patroni images

```sh
P18=postgres@sha256:74935e72241653ca55e0414067e6d8763aceb8a810eb51b452253ec3dcfc4336
P19=postgres@sha256:9df2c846b8b9130f3877a30495d9931538954768602a64d32c415c44bd958e9c
docker build --build-arg BASE=$P18 -t patroni-pg19-locks:18.6 .
docker build --build-arg BASE=$P19 -t patroni-pg19-locks:19rc1 .
```

## One server: `run.sh NAME IMAGE arm.sh KIND LOCKS`

`KIND` is `stock` or `patroni`. `LOCKS` is `unset` or a number (for Patroni it goes into `bootstrap.dcs`). The script prints the setting and its source, locks distinct empty tables in one transaction until `out of shared memory` (3 times per lock mode), then runs `pg_dump -s` on a database with 12,000 tables. Output goes to `./out/NAME/`.

```sh
./run.sh stock-19       "$P19"                   arm.sh stock   unset   # 17,405
./run.sh patroni-19     patroni-pg19-locks:19rc1 arm.sh patroni unset   #  8,701, pg_dump fails
./run.sh patroni-18     patroni-pg19-locks:18.6  arm.sh patroni unset   # 14,669
./run.sh patroni-19-128 patroni-pg19-locks:19rc1 arm.sh patroni 128     # 17,405
./run.sh stock-18-256   "$P18"                   arm.sh stock   256
./run.sh stock-19-512   "$P19"                   arm.sh stock   512     # 1.26x stock-18-256
./run.sh stock-19-256   "$P19"                   arm.sh stock   256     # 0.63x stock-18-256
```

The numbers in the comments are ACCESS EXCLUSIVE counts at `max_connections = 100`; see `out/NAME/lockcap.txt` (columns: mode, repetition, count, SQLSTATE, message).

## The fix on a running cluster: `fix.sh`

Starts Patroni on 19rc1 with nothing set, measures, then runs `patronictl edit-config -p 'max_locks_per_transaction=128'` and `patronictl restart`, and measures again.

```sh
./run.sh fix patroni-pg19-locks:19rc1 fix.sh
```

`out/fix/` holds `show-config` before and after, `settings.*.txt`, `lockcap.txt`, `pg_dump.txt` and the Patroni log.

## Limits

PostgreSQL 19 RC 1, Patroni 4.1.5, a single member, empty tables. Lock counts depend on `max_connections` and other settings; compare ratios, not absolute numbers, with your own servers.

## Licence

The files in this folder are MIT-licensed (see `LICENSE`). The images they build contain Debian, PostgreSQL, etcd and Patroni under those projects' own licences.
