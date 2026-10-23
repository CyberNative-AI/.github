#!/bin/bash
# Phase G: one primary per (version, FPW); base backup, then CHECKPOINT + 5% UPDATE, archived WAL.
# usage: gen.sh TAG SCALE FPW(on|off)
set -euo pipefail
TAG=$1; SCALE=$2; FPW=$3
W=/work/$TAG
rm -rf "$W"; mkdir -p "$W/arch"; chown -R postgres:postgres "$W"
P() { gosu postgres "$@"; }
Q() { P psql -X -h /tmp -At -v ON_ERROR_STOP=1 postgres -c "$1"; }
P initdb -D "$W/primary" -A trust --no-sync >/dev/null
cat >> "$W/primary/postgresql.auto.conf" <<CONF
listen_addresses = ''
unix_socket_directories = '/tmp'
archive_mode = on
archive_command = 'test ! -f $W/arch/%f && cp %p $W/arch/%f'
full_page_writes = $FPW
CONF
P pg_ctl -D "$W/primary" -l "$W/primary.log" -w start >/dev/null
P pgbench -h /tmp -q -i -s "$SCALE" postgres 2>&1 | tail -1
Q "ALTER TABLE pgbench_accounts SET (autovacuum_enabled = false)"
P pg_basebackup -h /tmp -D "$W/base" -X stream -c fast
Q "CHECKPOINT"
L0=$(Q "SELECT pg_current_wal_lsn()")
T0=$(date +%s.%N)
Q "UPDATE pgbench_accounts SET abalance = abalance + 1 WHERE aid % 20 = 0"
T1=$(date +%s.%N)
L1=$(Q "SELECT pg_current_wal_lsn()")
SEG=$(Q "SELECT pg_walfile_name('$L1')")
Q "SELECT pg_switch_wal()" >/dev/null
for i in $(seq 600); do [ -f "$W/arch/$SEG" ] && break; sleep 1; done
[ -f "$W/arch/$SEG" ] || { echo "ABORT: $SEG not archived"; exit 3; }
WALB=$(Q "SELECT pg_wal_lsn_diff('$L1','$L0')")
HEAPPAGES=$(Q "SELECT pg_relation_size('pgbench_accounts')/8192")
IDXPAGES=$(Q "SELECT pg_relation_size('pgbench_accounts_pkey')/8192")
VER=$(Q "SELECT version()")
FPWSHOW=$(Q "SHOW full_page_writes")
P pg_ctl -D "$W/primary" -m fast -w stop >/dev/null
rm -rf "$W/primary"
cat > "$W/gen.json" <<J
{"tag":"$TAG","scale":$SCALE,"fpw":"$FPWSHOW","version":"$VER","update_lsn_start":"$L0","update_lsn_end":"$L1",
 "last_segment":"$SEG","update_wal_bytes":$WALB,"update_seconds":$(awk "BEGIN{print $T1-$T0}"),
 "heap_pages_after":$HEAPPAGES,"pkey_pages_after":$IDXPAGES,
 "arch_bytes":$(du -sb "$W/arch" | cut -f1),"base_bytes":$(du -sb "$W/base" | cut -f1)}
J
chown -R postgres:postgres "$W"
cat "$W/gen.json"
