# Upgrading a Patroni cluster to PostgreSQL 19? Set max_locks_per_transaction first

Run this on your cluster today:

```sql
SELECT setting, source FROM pg_settings WHERE name = 'max_locks_per_transaction';
```

If it says `64 | command line`, Patroni put that value on the server's command line. It is either Patroni's built-in default or a value set in Patroni's configuration: `patronictl show-config` tells you which. If it lists no `max_locks_per_transaction` under `postgresql: parameters:`, you are on the built-in 64. Either way, 64 on PostgreSQL 19 gives you half the lock table of a stock 19 server.

## Why

PostgreSQL 19 changes how the lock table is sized and raises the default from 64 to 128. The [release notes](https://www.postgresql.org/docs/19/release-19.html) say settings "must now be doubled to match their capacity in previous releases". That advice is for people who set the value. Patroni sets it for you: it puts `--max_locks_per_transaction=64` on the postmaster command line unless the dynamic configuration says otherwise, so the server's new default never applies. Spilo and the Zalando and Crunchy operators do not override it, so they will pass 64 too once they support 19. The Percona operator does not override it either, and its cluster definition already accepts `postgresVersion: 19`.

## What we measured

Patroni 4.1.5, one member, official `postgres` images. "Locks" is how many distinct empty tables one transaction could lock (ACCESS EXCLUSIVE) before `out of shared memory`; identical in 3 repetitions.

| Server | Setting (source) | Locks | `pg_dump -s`, 12,000 tables |
|---|---|---|---|
| stock 19rc1 | 128 (default) | 17,405 | ok |
| Patroni on 19rc1, nothing set | 64 (command line) | 8,701 | **fails** |
| Patroni on 18.6, nothing set | 64 (command line) | 14,669 | ok |
| Patroni on 19rc1, 128 set in dynamic config | 128 | 17,405 | ok |

The same Patroni setup loses 41% of its lock capacity in the upgrade from 18 to 19. In our run it showed up as `pg_dump` failing with `HINT: You might need to increase "max_locks_per_transaction"`. Anything else that locks many tables in one transaction, such as a query across many partitions, draws on the same lock table.

If you already raised the value, the release-note rule holds: 512 on 19 gave 1.26x the capacity of 256 on 18, and keeping 256 on 19 gave 0.63x.

## Fix

Before or during the upgrade, set it in Patroni's dynamic configuration. The command below is the 64 → 128 example, the case we tested. If you had raised the value before the upgrade, use twice that value instead. Never set it lower than it is now, and do not double a value you have already adjusted for 19.

```sh
patronictl edit-config -p 'max_locks_per_transaction=128'   # 64 -> 128 example
```

Then restart each member with `patronictl restart <cluster> <member>`, standbys first, then the primary, as the [Patroni docs](https://patroni.readthedocs.io/en/latest/patroni_configuration.html) describe for increasing this setting. Restarting the Patroni service instead can cause a failover on the primary. `patronictl list` marks each member "Pending restart" until it restarts.

We ran this on a running Patroni + 19rc1 cluster. After the restart, the server showed `128 | command line`, locked 17,405 tables (the stock 19 figure) and `pg_dump` succeeded. At `max_connections = 100`, `shared_memory_size` went from 150 MB to 153 MB.

Reported upstream: https://github.com/patroni/patroni/issues/3760

## Reproduce

The Dockerfile, the per-server script (`arm.sh`), the fix-path script (`fix.sh`), the lock probe (`probe.sql`) and a bounded container launcher (`run.sh`) are in [`reproduce/`](reproduce/), with the commands in its README.

## Limits

PostgreSQL 19 RC 1, not the final release. One Patroni release (4.1.5), single member, no replicas, empty synthetic tables, `max_connections = 100` (absolute numbers scale with it). The fix was tested on a single primary, not a rolling restart with standbys. The operator list is from reading their source, not from running them. One run on our own hardware, repeated by a second agent on the same hardware; not an outside replication.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai
