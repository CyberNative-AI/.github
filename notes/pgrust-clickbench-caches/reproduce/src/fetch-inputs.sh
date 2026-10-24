#!/bin/bash
# Download the exact inputs we used and check their sha256. usage: bash src/fetch-inputs.sh DIR
# DIR/dl gets the pgrust tarball, DIR/data the 16 parquet partitions; ./upstream gets the two
# ClickBench files from pull request #2751's head commit (not copied here: ClickBench is CC BY-NC-SA 4.0).
set -eu
DIR=$1; HERE=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p "$DIR/dl" "$DIR/data" "$HERE/upstream"
PR=https://raw.githubusercontent.com/malisper/ClickBench/deabb4a553195570e1ad3e738146759cafa4ae02/pgrust
curl -fsSL -o "$HERE/upstream/pgrust-create.sql" "$PR/create.sql"
curl -fsSL -o "$HERE/upstream/pgrust-queries.sql" "$PR/queries.sql"
curl -fsSL -o "$DIR/dl/pgrust-0.4-beta-linux-x86_64.tar.gz" https://pgrust.com/downloads/v0.4-beta/pgrust-0.4-beta-linux-x86_64.tar.gz
for i in $(seq 0 15); do
  curl -fsSL -o "$DIR/data/hits_$i.parquet" "https://datasets.clickhouse.com/hits_compatible/athena_partitioned/hits_$i.parquet"
done
python3 -I "$HERE/src/check_inputs.py" "$HERE/inputs.sha256" "$HERE/upstream" "$DIR/dl" "$DIR/data"
python3 -I "$HERE/src/determinize.py" "$HERE/upstream/pgrust-queries.sql" "$HERE/src/queries-determinized.sql"
