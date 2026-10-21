#!/bin/bash
# Patroni on PostgreSQL 19 with nothing set, then the fix on the running cluster:
#   patronictl edit-config -p 'max_locks_per_transaction=128'; patronictl restart
# Records show-config, settings, lock counts and pg_dump before and after. Output -> /out
# Runs as root inside the container built from ./Dockerfile; postgres work drops to uid postgres via gosu.
set -u
OUT=/out; NPROBE=20000; NDUMP=12000; BATCH=500
mkdir -p $OUT; exec > >(tee -a $OUT/fix.log) 2>&1
ts(){ date -u +%FT%T.%3NZ; }
step(){ echo; echo "## $* $(ts)"; }
mkdir -p /pgdata/db /pgdata/etcd /var/run/postgresql
chown -R postgres:postgres /pgdata /var/run/postgresql; chmod 700 /pgdata/db
G="gosu postgres"
PSQL="$G psql -X -h /var/run/postgresql -U postgres -v ON_ERROR_STOP=1"
C="$G patronictl -c /pgdata/patroni.yml"

$G etcd --name e1 --data-dir /pgdata/etcd --listen-client-urls http://127.0.0.1:2379 \
   --advertise-client-urls http://127.0.0.1:2379 --listen-peer-urls http://127.0.0.1:2380 \
   --initial-advertise-peer-urls http://127.0.0.1:2380 --initial-cluster e1=http://127.0.0.1:2380 \
   > $OUT/etcd.log 2>&1 &
sleep 3
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
chown postgres:postgres /pgdata/patroni.yml; cp /pgdata/patroni.yml $OUT/patroni.yml
$G patroni /pgdata/patroni.yml > $OUT/patroni.log 2>&1 &

ready(){ # leader running, postgres accepting, and no pending restart flag
  for i in $(seq 1 90); do
    L=$($C list -f json 2>/dev/null)
    if echo "$L" | grep -q '"State": "running"' && ! echo "$L" | grep -q 'Pending restart' \
       && $G pg_isready -h /var/run/postgresql -q; then return 0; fi
    sleep 2
  done; return 1; }
ready; echo "ready rc=$?"; sleep 12
patroni --version; cp /opt/patroni/freeze.txt /opt/patroni/versions.txt $OUT/ 2>/dev/null

measure(){ # $1 = label, $2 = repetitions
  $PSQL -AtF'|' -c "select name, setting, source from pg_settings where name in ('max_locks_per_transaction','max_connections','shared_memory_size') order by name" | tee $OUT/settings.$1.txt
  tr '\0' ' ' < /proc/$(head -1 /pgdata/db/postmaster.pid)/cmdline | tee $OUT/postmaster-cmdline.$1.txt; echo
  for mode in 'ACCESS EXCLUSIVE' 'ACCESS SHARE'; do
    for rep in $(seq 1 $2); do
      r=$($PSQL -d probe -AtF'|' -c "select n, state, msg from lockcap('$mode')" 2>&1)
      echo "LOCKCAP|$1|$mode|$rep|$r|$(ts)" | tee -a $OUT/lockcap.txt
    done
  done
  $G pg_dump -h /var/run/postgresql -U postgres -s -d dumpk -f /dev/null 2> $OUT/pg_dump.$1.stderr; rc=$?
  echo "PGDUMP|$1|rc=$rc|$(ts)" | tee -a $OUT/pg_dump.txt; tail -3 $OUT/pg_dump.$1.stderr | cut -c1-200
}

step "show-config before"; $C show-config | tee $OUT/show-config.before.yml
step "create tables"
$PSQL -qc "create database probe" -c "create database dumpk"
mk(){ awk -v n=$1 -v b=$BATCH 'BEGIN{for(i=1;i<=n;i++){if((i-1)%b==0)print "BEGIN;"; printf "CREATE TABLE t%d (id int);\n", i; if(i%b==0||i==n)print "COMMIT;"}}'; }
mk $NPROBE | $PSQL -q -d probe; echo "probe create rc=${PIPESTATUS[1]}"
mk $NDUMP | $PSQL -q -d dumpk; echo "dumpk create rc=${PIPESTATUS[1]}"
$PSQL -q -d probe < /scripts/probe.sql   # root reads the file, so its permissions do not matter
step "measure before"; measure before 1

step "edit-config"; $C edit-config -p 'max_locks_per_transaction=128' --force
sleep 15
step "list after edit-config"; $C list | tee $OUT/list.pending.txt
$PSQL -AtF'|' -c "select name, setting, source, pending_restart from pg_settings where name = 'max_locks_per_transaction'" | tee $OUT/settings.pending.txt
step "show-config after"; $C show-config | tee $OUT/show-config.after.yml
step "restart"; $C restart demo m1 --force
ready; echo "ready rc=$?"
step "list after restart"; $C list | tee $OUT/list.after.txt
step "measure after"; measure after 3

step "shutdown"
for p in $(ps -eo pid,comm | awk '$2=="patroni"{print $1}'); do kill -TERM $p; done
for i in $(seq 1 30); do [ -z "$(ps -eo comm | awk '$1=="patroni"')" ] && break; sleep 1; done
for p in $(ps -eo pid,comm | awk '$2=="etcd"{print $1}'); do kill -TERM $p; done
echo "## end $(ts)"
chmod -R a+rX $OUT
