#!/usr/bin/env bash
# Runs the four scanners over the synthetic inputs. Usage: run_scanners.sh WORKDIR REP
# WORKDIR must hold inputs/ from make_inputs.py; output goes to WORKDIR/out/repREP.
# Same commands and image digests as our October 22 runs; only our host's paths and job labels
# were replaced by WORKDIR. Build the pip-audit image first:
#   docker build -t local/pip-audit:2.10.1 -f pip-audit.Dockerfile .
set -u
B=$1; REP=$2
IN=$B/inputs; O=$B/out/rep$REP; mkdir -p $O $B/cache/trivy $B/cache/grype
TRIVY=aquasec/trivy@sha256:790fd66d1697395d8693d1acaa1ea702406a20f109b6fc7bac8db623eca6c06c
GRYPE=anchore/grype@sha256:621d56d1d68106b787022c81546f7e0a36202a25d1239f0c20195fab8c16f7ea
OSV=ghcr.io/google/osv-scanner@sha256:4f3b7e2c64b9d38a5febc5a7e4a3dfef1d1362f726dea7a2ef4762b46469fcd0
PA=local/pip-audit:2.10.1
for V in T M C N; do
 for F in F1 F2 F3 F4; do
  P=$IN/$V/$F
  if [ $F = F4 ]; then TCMD="rootfs"; else TCMD="fs"; fi
  docker run --rm -v $P:/in:ro -v $B/cache/trivy:/root/.cache/trivy $TRIVY \
     $TCMD --scanners vuln --format json --quiet /in > $O/trivy-$V-$F.json 2> $O/trivy-$V-$F.err; echo $? > $O/trivy-$V-$F.rc
  docker run --rm -v $P:/in:ro -v $B/cache/grype:/root/.cache/grype -e GRYPE_DB_CACHE_DIR=/root/.cache/grype $GRYPE \
     dir:/in -o json > $O/grype-$V-$F.json 2> $O/grype-$V-$F.err; echo $? > $O/grype-$V-$F.rc
  docker run --rm -v $P:/in:ro $OSV \
     scan source -r --format json /in > $O/osv-$V-$F.json 2> $O/osv-$V-$F.err; echo $? > $O/osv-$V-$F.rc
  if [ $F = F1 ]; then
   for S in pypi osv; do
    docker run --rm -v $P:/in:ro $PA \
      pip-audit -r /in/requirements.txt --no-deps --disable-pip -s $S -f json > $O/pa_$S-$V-$F.json 2> $O/pa_$S-$V-$F.err; echo $? > $O/pa_$S-$V-$F.rc
   done
  elif [ $F = F4 ]; then
   for S in pypi osv; do
    docker run --rm -v $P:/in:ro $PA \
      pip-audit --path /in/usr/local/lib/python3.12/site-packages -s $S -f json > $O/pa_$S-$V-$F.json 2> $O/pa_$S-$V-$F.err; echo $? > $O/pa_$S-$V-$F.rc
   done
  fi
 done
done
docker run --rm $TRIVY --version > $O/ver-trivy.txt 2>&1
docker run --rm -v $B/cache/trivy:/root/.cache/trivy $TRIVY version --format json > $O/ver-trivy-db.json 2>&1
docker run --rm -v $B/cache/grype:/root/.cache/grype -e GRYPE_DB_CACHE_DIR=/root/.cache/grype $GRYPE db status -o json > $O/ver-grype-db.json 2>&1
docker run --rm $GRYPE version > $O/ver-grype.txt 2>&1
docker run --rm $OSV --version > $O/ver-osv.txt 2>&1
docker run --rm $PA pip-audit --version > $O/ver-pipaudit.txt 2>&1
date -u +%FT%TZ > $O/done.txt
