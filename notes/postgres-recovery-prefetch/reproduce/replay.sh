#!/bin/bash
# Phase R: cold archive recovery of the same base + WAL with recovery_prefetch=$PF.
# usage: replay.sh TAG PF(try|off) REP
set -euo pipefail
TAG=$1; PF=$2; REP=$3
W=/work/$TAG; S=$W/standby; OUT=$W/runs/$PF-$REP
mkdir -p "$OUT"; rm -rf "$S"
cp -a "$W/base" "$S"
cat >> "$S/postgresql.auto.conf" <<CONF
listen_addresses = ''
unix_socket_directories = '/tmp'
archive_mode = off
hot_standby = on
recovery_prefetch = $PF
restore_command = 'cp $W/arch/%f %p'
CONF
touch "$S/recovery.signal"; chown -R postgres:postgres "$S" "$W/runs"
sync
if [ "${EVICT:-1}" = 1 ]; then find "$S" "$W/arch" -type f -exec dd if={} iflag=nocache count=0 status=none \;
fi
sync
cat /sys/fs/cgroup/io.stat > "$OUT/io0"
T0=$(date +%s.%N)
gosu postgres pg_ctl -D "$S" -l "$OUT/pg.log" start >/dev/null
DONE=0
for i in $(seq 7200); do
  sleep 1
  gosu postgres psql -X -h /tmp -At -F, postgres -c "SELECT now(),pg_last_wal_replay_lsn(),prefetch,hit,skip_init,skip_new,skip_fpw,skip_rep,wal_distance,block_distance,io_depth FROM pg_stat_recovery_prefetch" >> "$OUT/prefetch.csv" 2>/dev/null || true
  if grep -q "database system is ready to accept connections" "$OUT/pg.log"; then DONE=1; break; fi
  if grep -qE "FATAL|PANIC" "$OUT/pg.log"; then break; fi
done
T1=$(date +%s.%N)
cat /sys/fs/cgroup/io.stat > "$OUT/io1"
gosu postgres psql -X -h /tmp -At -F, postgres -c "SELECT prefetch,hit,skip_init,skip_new,skip_fpw,skip_rep FROM pg_stat_recovery_prefetch" > "$OUT/prefetch_final.csv" 2>/dev/null || true
gosu postgres pg_ctl -D "$S" -m fast -w stop >/dev/null || true
echo "{\"tag\":\"$TAG\",\"pf\":\"$PF\",\"rep\":\"$REP\",\"evict\":\"${EVICT:-1}\",\"done\":$DONE,\"t0\":$T0,\"t1\":$T1}" > "$OUT/run.json"
grep -E "redo (starts|done)|recovery complete|ready to accept" "$OUT/pg.log" || true
rm -rf "$S"
chown -R postgres:postgres "$W/runs"
