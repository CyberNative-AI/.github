#!/bin/bash
# In-container runner for pgrust 0.4-beta (ClickBench cache modes; see ../README.md).
# usage: pg_run.sh SIZE NPART "MODES" QUERYFILE OUTFILE [REPS]
#   SIZE   label of the data directory (one database per size, loaded once)
#   NPART  number of hits_<i>.parquet partitions to COPY (0..NPART-1) from /data
#   MODES  space-separated pgrust.condition_cache values (full rows granule off)
#   QUERYFILE one statement per line; OUTFILE JSONL appended
#   REPS   timed runs per query after a restart (default 3, ClickBench)
# Config follows upstream/pgrust-install (PR #2751 head deabb4a5) with RAM and threads fixed to the
# container budget (MEM_KB, THREADS) instead of the host's /proc/meminfo and nproc.
set -u
SIZE=$1; NPART=$2; MODES=$3; QF=$4; OUT=$5; REPS=${6:-3}
P=/scratch/install
D=/scratch/pg-$SIZE
SOCK=/tmp/pgsock-$SIZE
PORT=5432
MEM_KB=${MEM_KB:-25165824}   # 24 GiB
THREADS=${THREADS:-8}
PSQL="$P/bin/psql -X -h $SOCK -p $PORT -U postgres"
mkdir -p "$SOCK" "$(dirname "$OUT")"
export RUST_MIN_STACK=67108864
ulimit -s 65520 2>/dev/null || true

if [ ! -x "$P/bin/postgres" ]; then
  mkdir -p "$P" && tar -xzf /dl/pgrust-0.4-beta-linux-x86_64.tar.gz --strip-components=1 -C "$P"
fi

start() { "$P/bin/postgres" -D "$D" -p $PORT >> "$D/server.log" 2>&1 < /dev/null &
  for i in $(seq 1 240); do $PSQL -tAc 'SELECT 1' >/dev/null 2>&1 && return 0; sleep 0.25; done
  echo "start failed" >&2; tail -20 "$D/server.log" >&2; return 1; }
stop() { local pidf="$D/postmaster.pid"
  [ -f "$pidf" ] && kill -INT "$(head -1 "$pidf")" 2>/dev/null
  for i in $(seq 1 240); do [ -f "$pidf" ] && kill -0 "$(head -1 "$pidf")" 2>/dev/null || return 0; sleep 0.25; done
  echo "stop timeout" >&2; return 1; }

if [ ! -f "$D/LOADED" ]; then
  rm -rf "$D"
  "$P/bin/initdb" -D "$D" --no-locale --encoding=UTF8 -U postgres -A trust >/dev/null || exit 1
  cat >> "$D/postgresql.conf" <<CONF
effective_cache_size=$((MEM_KB - MEM_KB / 4))kB
work_mem=$((MEM_KB / (2 * THREADS)))kB
max_wal_size=32GB
max_worker_processes=$((THREADS + 15))
max_parallel_workers=${THREADS}
max_parallel_workers_per_gather=${THREADS}
max_parallel_maintenance_workers=$((THREADS / 2))
listen_addresses=''
unix_socket_directories='$SOCK'
io_method=sync
max_stack_depth=60000
autovacuum=off
pgrust.gravity_grant_mb=$((MEM_KB / 4 / 1024))
pgrust.gravity_statement_pool_fraction=1
pgrust.pgrc_part_cache_mb=$((MEM_KB * 3 / 8 / 1024))
pgrust.condition_cache=full
pgrust.dict_filter_cache=on
pgrust.zone_store=on
include_if_exists 'mode.conf'
CONF
  start || exit 1
  t0=$(date +%s.%N)
  $PSQL -tAc "CREATE DATABASE test" >/dev/null
  $PSQL -v ON_ERROR_STOP=1 -d test -q -f /lab/upstream/pgrust-create.sql || exit 1
  for i in $(seq 0 $((NPART - 1))); do
    $PSQL -v ON_ERROR_STOP=1 -d test -q -c "COPY hits FROM '/data/hits_$i.parquet' WITH (FORMAT 'parquet', COERCE_EPOCH true)" || exit 1
  done
  $PSQL -v ON_ERROR_STOP=1 -d test -q -c "ANALYZE hits" || exit 1
  t1=$(date +%s.%N)
  rows=$($PSQL -d test -tAc 'SELECT count(*) FROM hits')
  printf '{"event":"load","size":"%s","npart":%s,"rows":%s,"t0":%s,"t1":%s}\n' "$SIZE" "$NPART" "$rows" "$t0" "$t1" >> "$OUT"
  stop; touch "$D/LOADED"
fi

esc() { python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))' 2>/dev/null || sed 's/"/\\"/g' | tr '\n' ' ' | sed 's/^/"/;s/$/"/'; }

for MODE in $MODES; do
  if [ "$MODE" = "full" ] || [ "$MODE" = "rows" ] || [ "$MODE" = "granule" ] || [ "$MODE" = "off" ]; then
    echo "pgrust.condition_cache=$MODE" > "$D/mode.conf"
  else echo "bad mode $MODE" >&2; exit 2; fi
  q=0
  while IFS= read -r query || [ -n "$query" ]; do
    [ -z "$query" ] && continue
    stop; start || exit 1
    got=$($PSQL -d test -tAc "SHOW pgrust.condition_cache" 2>&1)
    for r in $(seq 1 "$REPS"); do
      res=$(printf '\\timing\n%s\n' "$query" | $PSQL -d test -t 2>&1); rc=$?
      ms=$(printf '%s\n' "$res" | grep -oP 'Time:\s+\K[0-9]+\.[0-9]+' | tail -n1)
      body=$(printf '%s\n' "$res" | grep -v '^Time:')
      err=0; printf '%s\n' "$body" | grep -q '^ERROR\|psql: error' && err=1
      h=$(printf '%s' "$body" | sha256sum | cut -c1-16)
      printf '{"event":"run","size":"%s","mode":"%s","mode_shown":"%s","q":%d,"run":%d,"ms":%s,"rc":%d,"err":%d,"res_sha":"%s"}\n' \
        "$SIZE" "$MODE" "$got" "$q" "$r" "${ms:-null}" "$rc" "$err" "$h" >> "$OUT"
      [ "$err" = 1 ] && printf '%s\n' "$body" | head -5 > "$(dirname "$OUT")/err-${TAG:-t}-$SIZE-$MODE-q$q-r$r.txt"
    done
    # explain after the timed runs (warm, same server): secondary readout of what the hot run touched
    printf 'EXPLAIN (ANALYZE, VERBOSE) %s\n' "$query" | $PSQL -d test -t > "$(dirname "$OUT")/explain-${TAG:-t}-$SIZE-$MODE-q$q.txt" 2>&1
    q=$((q + 1))
  done < "$QF"
done
# Staleness arm (STALE=1): after the timed modes, per mode: warm the caches with the two count-only
# queries (q1, q20), mutate the table, rerun them on the same warm server, then restart with every
# cache off and recount. A warm answer that differs from the cold recount is a stale answer.
if [ "${STALE:-0}" = 1 ]; then
  Q1="SELECT COUNT(*) FROM hits WHERE AdvEngineID <> 0;"
  Q20="SELECT COUNT(*) FROM hits WHERE URL LIKE '%google%';"
  cnt() { $PSQL -d test -tAc "$1" 2>&1 | head -1; }
  for MODE in full rows granule off; do
    for MUT in insert delete; do
      echo "pgrust.condition_cache=$MODE" > "$D/mode.conf"; stop; start || exit 1
      for r in 1 2 3; do cnt "$Q1" >/dev/null; cnt "$Q20" >/dev/null; done
      b1=$(cnt "$Q1"); b20=$(cnt "$Q20")
      if [ "$MUT" = insert ]; then
        m=$($PSQL -d test -Ac "INSERT INTO hits SELECT * FROM hits WHERE AdvEngineID <> 0 LIMIT 1000" 2>&1 | head -2 | tr '\n' ' ')
        m="$m / $($PSQL -d test -Ac "INSERT INTO hits SELECT * FROM hits WHERE URL LIKE '%google%' LIMIT 50" 2>&1 | head -2 | tr '\n' ' ')"
      else
        m=$($PSQL -d test -Ac "DELETE FROM hits WHERE WatchID IN (SELECT WatchID FROM hits WHERE AdvEngineID <> 0 LIMIT 500)" 2>&1 | head -2 | tr '\n' ' ')
        m="$m / $($PSQL -d test -Ac "DELETE FROM hits WHERE WatchID IN (SELECT WatchID FROM hits WHERE URL LIKE '%google%' LIMIT 20)" 2>&1 | head -2 | tr '\n' ' ')"
      fi
      w1=$(cnt "$Q1"); w20=$(cnt "$Q20")
      echo "pgrust.condition_cache=off" > "$D/mode.conf"; echo "pgrust.dict_filter_cache=off" >> "$D/mode.conf"; echo "pgrust.zone_store=off" >> "$D/mode.conf"
      stop; start || exit 1
      c1=$(cnt "$Q1"); c20=$(cnt "$Q20")
      printf '{"event":"stale","mode":"%s","mut":"%s","mut_out":"%s","before_q1":"%s","before_q20":"%s","warm_q1":"%s","warm_q20":"%s","cold_q1":"%s","cold_q20":"%s"}\n' \
        "$MODE" "$MUT" "$m" "$b1" "$b20" "$w1" "$w20" "$c1" "$c20" >> "$OUT"
    done
  done
fi
stop
exit 0
