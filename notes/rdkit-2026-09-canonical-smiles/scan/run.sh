#!/bin/bash
# The full scan with plain Docker. Each container runs the command we ran. This script was written for publication
# and has not been run end to end. It stops at the first failed step.
# usage: bash run.sh W    W = a new, empty work folder. Needs Docker,
# about 5 GB of disk, network for the setup steps only, and about 1.5 h on 6 CPUs for the scan.
set -eu
W=$(cd "${1:?usage: run.sh WORK_FOLDER}" && pwd); S=$(cd "$(dirname "$0")" && pwd); O=$W/out
IMG=python:3.12-slim@sha256:05cda9777409a9c3ffddd94a4c476b79f0769a0b4857f0c7ed9226b6800b0d6f
declare -A VER=([V1]=2025.3.6 [V2]=2025.9.6 [V3]=2026.3.6 [V4]=2026.9.1 [V4L]=2026.9.1)

# Setup (network): ChEMBL 37 structures, input files, one venv per release.
mkdir -p "$W/data" "$W/venvs" "$O/P1"
curl -fL -o "$W/data/chembl_37_chemreps.txt.gz" \
  https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/chembl_37/chembl_37_chemreps.txt.gz
echo "ea6181ce8dc7af41974e35b92e1febb0c9dcbe2c62f7ccc4a5d983ac19f696e7  $W/data/chembl_37_chemreps.txt.gz" | sha256sum -c
docker run --rm -v "$S:/src:ro" -v "$W/data:/data" $IMG python -I /src/build_inputs.py /data
for v in 2025.3.6 2025.9.6 2026.3.6 2026.9.1; do
  docker run --rm -v "$S:/src:ro" -v "$W/venvs:/venvs" $IMG sh -c \
    "python -m venv /venvs/rdkit-$v && /venvs/rdkit-$v/bin/pip install -q -r /src/freeze/rdkit-$v.txt"
done

# Scan (no network). Modes: A all of ChEMBL, B 100k sample, D repeat of B for 2026.09.1, T tautomers.
one() { # mode arm input outdir chunk timeout
  local m=$1 a=$2 in=$3 od=$4 ch=$5 to=$6 v=${VER[$2]} env=()
  [ "$a" = V4L ] && env=(-e RDK_USE_LEGACY_RING_FINDING=1)
  docker run --rm --cpus 6 --memory 8g --network none ${env[@]+"${env[@]}"} -v "$W/venvs:/venvs:ro" \
    -v "$W/data:/data:ro" -v "$S:/src:ro" -v "$O:/out" $IMG sh -c \
    "/venvs/rdkit-$v/bin/python -I /src/controls.py > /out/controls-$m-$a.json && /venvs/rdkit-$v/bin/python -I /src/drive.py /venvs/rdkit-$v/bin/python $m /data/$in /out/$od --jobs 6 --chunk $ch --timeout $to"
}
for a in V1 V2 V3 V4 V4L; do one B $a sample100k.tsv B-$a 5000 900; done
one B V4 sample100k.tsv D 5000 900
for a in V3 V4 V4L; do one T $a taut20k.tsv T-$a 100 300; done
for a in V1 V2 V3 V4 V4L; do one A $a all.tsv A-$a 5000 900; done

# Atom-order scan of the molecules with double-bond stereo, 2025.09.6 and 2026.09.1.
for v in 2025.9.6 2026.9.1; do
  docker run --rm --cpus 6 --memory 8g --network none -v "$W/venvs:/venvs:ro" -v "$W/data:/data:ro" \
    -v "$S:/src:ro" -v "$O/P1:/out" $IMG sh -c \
    "cd /out && mkdir -p $v && split -n l/6 -d /data/dbstereo.tsv /out/$v/part. && pids=; for p in /out/$v/part.0?; do timeout 3300 /venvs/rdkit-$v/bin/python -I /src/dbscan.py \$p \$p.jsonl & pids=\"\$pids \$!\"; done; rc=0; for q in \$pids; do wait \$q || rc=1; done; exit \$rc"
done

# Score (about 15 GB of RAM).
python3 -I "$S/score.py" "$O" "$W/scored.json"
python3 -I "$S/p1_sets.py" "$W/data/dbstereo.tsv" "$O/P1/2025.9.6" "$O/P1/2026.9.1" "$W/P1_both.json" > "$W/P1_sets.json"
