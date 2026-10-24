#!/bin/bash
# One replicate in one container: load 16 partitions once, then arms T, D and S (../README.md).
set -u
O=/scratch/out
N=${NPART:-16}   # 16 as in the README; 1 only for the pipeline dry run
mkdir -p "$O"
sha256sum /dl/pgrust-0.4-beta-linux-x86_64.tar.gz $(seq -f "/data/hits_%g.parquet" 0 $((N - 1))) > "$O/inputs.sha256"
TAG=t bash /lab/src/pg_run.sh s$N $N "full rows granule off" /lab/upstream/pgrust-queries.sql "$O/T.jsonl" 3 || exit 1
TAG=d bash /lab/src/pg_run.sh s$N $N "full rows granule off" /lab/src/queries-determinized.sql "$O/D.jsonl" 2 || exit 1
STALE=1 TAG=s bash /lab/src/pg_run.sh s$N $N "" /dev/null "$O/S.jsonl" 1 || exit 1
echo done > "$O/DONE"
