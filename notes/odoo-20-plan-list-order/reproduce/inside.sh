#!/bin/bash
# Runs inside the container as root: PostgreSQL + Odoo 20, no network. Called by rerun.sh.
# 1. build the dataset with construct.py and check it against data/ (byte-identical)
# 2. fresh database, install Manufacturing, load the shop with Odoo's clock at the export time
# 3. for each arm: copy the database, start Odoo with the clock frozen at the export time
#    (Mon 2026-11-02 08:00 UTC; Plan schedules from "now"), plan all open orders in the list's order,
#    export the work orders and score them with checker.py
set -euo pipefail
export TZ=UTC KIT=/bundle LANG=C.UTF-8 LC_ALL=C.UTF-8   # the base image has only the C.utf8 locale
OUT=/out; NOW="2026-11-02 08:00:00"; FT=/usr/local/lib/faketime/libfaketime.so.1
log() { echo "[$(date -u +%FT%TZ)] $*"; }
trap '[ -n "${HOST_UID:-}" ] && chown -R "$HOST_UID:${HOST_GID:-$HOST_UID}" $OUT || true' EXIT

log "dataset"
python3 /bundle/construct.py /tmp/data >/dev/null
diff -r /tmp/data /bundle/data && log "construct.py output matches data/"

PGBIN=/usr/lib/postgresql/16/bin; PGDATA=/var/lib/postgresql/data
mkdir -p $PGDATA /var/run/postgresql && chown -R postgres:postgres /var/lib/postgresql /var/run/postgresql
runuser -u postgres -- $PGBIN/initdb -D $PGDATA -U odoo -A trust -E UTF8 >/dev/null
runuser -u postgres -- $PGBIN/pg_ctl -D $PGDATA -l /tmp/pg.log -o "-c listen_addresses='' -c fsync=off" -w start >/dev/null
mkdir -p /var/lib/odoo && chown odoo:odoo /var/lib/odoo
OPTS=(--data-dir=/var/lib/odoo --db_host= --db_user=odoo --addons-path=/usr/lib/python3/dist-packages/odoo/addons)
ODOO=(runuser -u odoo -- odoo "${OPTS[@]}")
OSHELL=(runuser -u odoo -- odoo shell "${OPTS[@]}")
{ odoo --version; $PGBIN/postgres --version; } | tee $OUT/versions.txt

log "install Manufacturing"
"${ODOO[@]}" -d shop -i mrp --stop-after-init --log-level=warn
log "load the shop"
echo "$NOW" > /tmp/ft-now && chmod 666 /tmp/ft-now
env LD_PRELOAD=$FT FAKETIME_TIMESTAMP_FILE=/tmp/ft-now FAKETIME_NO_CACHE=1 FAKETIME_DONT_FAKE_MONOTONIC=1 SHOP_DATA=/bundle/data/base \
  "${OSHELL[@]}" -d shop --no-http --log-level=warn < /bundle/shop_load.py > $OUT/load.log 2>&1 || { tail -30 $OUT/load.log; exit 1; }
grep '^LOADED' $OUT/load.log

for arm in $ARMS; do
  case $arm in
    default) order="" ;;                                  # the list as a fresh user sees it
    deadline) order="date_deadline ASC" ;;                # Deadline header clicked once
    deadline_id) order="date_deadline ASC, id ASC" ;;     # same, ties broken by creation
    deadline_id_desc) order="date_deadline ASC, id DESC" ;;
    *) echo "unknown arm $arm"; exit 2 ;;
  esac
  runuser -u odoo -- createdb -h /var/run/postgresql -T shop plan_$arm
  log "plan, $arm"
  env LD_PRELOAD=$FT FAKETIME="$NOW" FAKETIME_DONT_FAKE_MONOTONIC=1 \
    "${ODOO[@]}" -d plan_$arm --db-filter="^plan_$arm\$" --http-interface=127.0.0.1 --http-port=8069 \
    --max-cron-threads=0 --workers=0 --log-level=warn > $OUT/server-$arm.log 2>&1 &
  server=$!
  for i in $(seq 120); do curl -sf -o /dev/null http://127.0.0.1:8069/web/login && break; sleep 1; done
  python3 /bundle/plan.py --db plan_$arm --order "$order" --log $OUT/$arm.ids.json
  kill $server; wait $server || true
  OUT=$OUT/$arm "${OSHELL[@]}" -d plan_$arm --no-http --log-level=warn < /bundle/export_plan.py
  python3 /bundle/checker.py --data /bundle/data/base --schedule $OUT/$arm.csv --json $OUT/$arm.check.json > $OUT/$arm.check.txt || true
done

python3 - "$OUT" $ARMS <<'PY'
import json, sys
out, arms = sys.argv[1], sys.argv[2:]
print("\n%-18s %10s %18s" % ("plan from", "late MOs", "tardiness (h)"))
for a in arms:
    c = json.load(open("%s/%s.check.json" % (out, a)))
    print("%-18s %10d %18.1f" % (a, c["late_orders"], c["total_tardiness_h"]))
print("\nchecker details: out/<arm>.check.txt; Odoo's planned work orders: out/<arm>.csv")
PY
