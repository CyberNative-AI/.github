#!/bin/bash
# One server per container: start it, report the setting, count locks, run pg_dump. Usage: arm.sh ARM KIND LOCKS   (KIND=stock|patroni; LOCKS=unset|N)
# Runs as root inside the container; postgres work drops to uid postgres via gosu. Output -> /out
set -u
ARM=$1; KIND=$2; LOCKS=$3
OUT=/out; NPROBE=80000; NDUMP=12000; BATCH=500
mkdir -p $OUT; exec > >(tee -a $OUT/arm.log) 2>&1
ts(){ date -u +%FT%T.%3NZ; }
echo "## server=$ARM kind=$KIND locks=$LOCKS start=$(ts)"
mkdir -p /pgdata/db /pgdata/etcd /var/run/postgresql
chown -R postgres:postgres /pgdata /var/run/postgresql; chmod 700 /pgdata/db
G="gosu postgres"
PSQL="$G psql -X -h /var/run/postgresql -U postgres -v ON_ERROR_STOP=1"
if [ "$KIND" = stock ]; then
  $G initdb -U postgres --auth=trust -E UTF8 -D /pgdata/db > $OUT/initdb.log 2>&1; echo "initdb rc=$?"
  OPT=""; [ "$LOCKS" != unset ] && OPT="-c max_locks_per_transaction=$LOCKS"
  $G pg_ctl -D /pgdata/db -l $OUT/server.log -w -t 120 ${OPT:+-o "$OPT"} start; echo "pg_ctl start rc=$?"
else
  $G etcd --name e1 --data-dir /pgdata/etcd --listen-client-urls http://127.0.0.1:2379 \
     --advertise-client-urls http://127.0.0.1:2379 --listen-peer-urls http://127.0.0.1:2380 \
     --initial-advertise-peer-urls http://127.0.0.1:2380 --initial-cluster e1=http://127.0.0.1:2380 \
     > $OUT/etcd.log 2>&1 &
  sleep 3
  DCSPG=""
  [ "$LOCKS" != unset ] && DCSPG="    postgresql:
      parameters:
        max_locks_per_transaction: $LOCKS"
  cat > /pgdata/patroni.yml <<YML
scope: demo
name: m1
log:
  level: INFO
restapi:
  listen: 127.0.0.1:8008
  connect_address: 127.0.0.1:8008
etcd3:
  hosts: 127.0.0.1:2379
bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
$DCSPG
  initdb:
    - encoding: UTF8
postgresql:
  listen: 127.0.0.1:5432
  connect_address: 127.0.0.1:5432
  data_dir: /pgdata/db
  pgpass: /pgdata/pgpass
  authentication:
    superuser:
      username: postgres
      password: synthetic-only
    replication:
      username: replicator
      password: synthetic-only
  pg_hba:
    - local all all trust
    - host all all 127.0.0.1/32 trust
    - host replication replicator 127.0.0.1/32 trust
YML
  chown postgres:postgres /pgdata/patroni.yml
  cp /pgdata/patroni.yml $OUT/patroni.yml
  $G patroni /pgdata/patroni.yml > $OUT/patroni.log 2>&1 &
  for i in $(seq 1 120); do
    if $G patronictl -c /pgdata/patroni.yml list 2>/dev/null | grep -q 'Leader.*running' && $G pg_isready -h /var/run/postgresql -q; then break; fi
    sleep 2
  done
  $G patronictl -c /pgdata/patroni.yml list; echo "patroni ready after ~$((i*2)) s"
  sleep 15
  patroni --version; cp /opt/patroni/freeze.txt /opt/patroni/versions.txt $OUT/ 2>/dev/null
fi
echo "## version"; $PSQL -Atc "select version()"
echo "## settings"
$PSQL -AtF'|' -c "select name, setting, source from pg_settings where name in ('max_locks_per_transaction','max_connections','max_prepared_transactions','max_worker_processes','max_wal_senders','autovacuum_worker_slots','autovacuum_max_workers','shared_memory_size','max_pred_locks_per_transaction','fast_path_lock_groups') order by name" | tee $OUT/settings.txt
PMPID=$(head -1 /pgdata/db/postmaster.pid)
echo "## postmaster pid=$PMPID cmdline"; tr '\0' ' ' < /proc/$PMPID/cmdline | tee $OUT/postmaster-cmdline.txt; echo
echo "## create tables $(ts)"
$PSQL -qc "create database probe" -c "create database dumpk"
mk(){ awk -v n=$2 -v b=$BATCH 'BEGIN{for(i=1;i<=n;i++){if((i-1)%b==0)print "BEGIN;"; printf "CREATE TABLE t%d (id int);\n", i; if(i%b==0||i==n)print "COMMIT;"}}'; }
mk probe $NPROBE | $PSQL -q -d probe; echo "probe create rc=${PIPESTATUS[1]}"
mk dumpk $NDUMP | $PSQL -q -d dumpk; echo "dumpk create rc=${PIPESTATUS[1]}"
$PSQL -Atc "select 'probe tables', count(*) from pg_class where relkind='r' and relname ~ '^t[0-9]+$'" -d probe
$PSQL -Atc "select 'dumpk tables', count(*) from pg_class where relkind='r' and relname ~ '^t[0-9]+$'" -d dumpk
$PSQL -q -d probe < /scripts/probe.sql   # root reads the file, so its permissions do not matter
echo "## lockcap $(ts)"
for mode in 'ACCESS EXCLUSIVE' 'ACCESS SHARE'; do
  for rep in 1 2 3; do
    r=$($PSQL -d probe -AtF'|' -c "select n, state, msg from lockcap('$mode')" 2>&1)
    echo "LOCKCAP|$mode|$rep|$r|$(ts)" | tee -a $OUT/lockcap.txt
  done
done
echo "## pg_dump $(ts)"
$G pg_dump -h /var/run/postgresql -U postgres -s -d dumpk -f /dev/null 2> $OUT/pg_dump.stderr; rc=$?
echo "PGDUMP|rc=$rc|$(ts)" | tee $OUT/pg_dump.txt; tail -5 $OUT/pg_dump.stderr | tee -a $OUT/pg_dump.txt
echo "## shutdown $(ts)"
if [ "$KIND" = stock ]; then $G pg_ctl -D /pgdata/db -m fast -w stop
else
  # stop patroni (it stops postgres), then etcd; copy server logs
  for p in $(ps -eo pid,comm | awk '$2=="patroni"{print $1}'); do kill -TERM $p; done
  for i in $(seq 1 30); do [ -z "$(ps -eo comm | awk '$1=="patroni"')" ] && break; sleep 1; done
  for p in $(ps -eo pid,comm | awk '$2=="etcd"{print $1}'); do kill -TERM $p; done
  cp -a /pgdata/db/log $OUT/pglog 2>/dev/null
  ls /pgdata/db/*.log 2>/dev/null && cp /pgdata/db/*.log $OUT/ 2>/dev/null
fi
echo "## FATAL scan"; grep -rn 'FATAL' $OUT --include='*.log' --include='*.txt' --include='*.stderr' | grep -v 'FATAL scan' > $OUT/fatal.txt; wc -l < $OUT/fatal.txt
echo "## end=$(ts)"
chmod -R a+rX $OUT
