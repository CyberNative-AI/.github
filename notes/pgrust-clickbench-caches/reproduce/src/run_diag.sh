#!/bin/bash
# Diagnostic run added after rep a (one container, 16 partitions): which cache gives the full/rows gains.
set -u
O=/scratch/out
mkdir -p "$O"
TAG=x bash /lab/src/pg_run_diag.sh s16 16 "full+nodict rows+nodict granule full" /lab/upstream/pgrust-queries.sql "$O/X.jsonl" 3 || exit 1
echo done > "$O/DONE"
