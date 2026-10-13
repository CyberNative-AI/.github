#!/bin/bash
# Host driver for the main matrix: build environments, probe servers, classify clients, run the matrix
# in four offline containers, merge and analyse. Calls the scripts in this directory unchanged.
#
# usage: harness/rerun/reproduce.sh WORKDIR
#   WORKDIR/envs/uv  uv 0.10.7 binary (x86_64-unknown-linux-gnu)    } see REPRODUCE.md for download
#   WORKDIR/envs/go  Go 1.26.9 linux-amd64 tree (tarball unpacked)  } and checksums
#   WORKDIR/out      must not exist; each invocation writes a fresh one
#   SKIP_SETUP=1     reuse environments already built in WORKDIR/envs (skips the only networked step)
# Bounds (environment variables, defaults shown; times in seconds):
#   CPUS=2 MEM=2g PIDS=512        per container, every step; the matrix runs 4 containers at once
#   SETUP_TIMEOUT=3600            each of the two setup containers
#   PHASE1_TIMEOUT=900 MATRIX_TIMEOUT=3600 MERGE_TIMEOUT=600
# Results: WORKDIR/out/merged/{RESULT.json,POSTHOC-gap.json}; compare with results/rerun/.
# On any failure, timeout or interruption the driver removes the containers it started (and only those),
# writes WORKDIR/out/INCOMPLETE, keeps whatever output exists, skips the merge and exits non-zero.
set -eu
H=$(cd "$(dirname "$0")/.." && pwd)
W=$(mkdir -p "$1" && cd "$1" && pwd)
IMG=node:22-bookworm
CPUS=${CPUS:-2} MEM=${MEM:-2g} PIDS=${PIDS:-512}
SETUP_TIMEOUT=${SETUP_TIMEOUT:-3600} PHASE1_TIMEOUT=${PHASE1_TIMEOUT:-900}
MATRIX_TIMEOUT=${MATRIX_TIMEOUT:-3600} MERGE_TIMEOUT=${MERGE_TIMEOUT:-600}
[ -x "$W/envs/uv" ] && [ -x "$W/envs/go/bin/go" ] || { echo "need $W/envs/uv and $W/envs/go (REPRODUCE.md)" >&2; exit 2; }
[ ! -e "$W/out" ] || { echo "$W/out exists; move it aside so its results are kept and not mixed" >&2; exit 2; }
mkdir -p "$W/scratch" "$W/out/phase1/probes" "$W/out/main-go" "$W/out/main-py" "$W/out/main-ts" "$W/out/aux" "$W/out/merged"

RID=$(date +%s)-$$
LOG=$W/out/driver.log
U=(--rm --user "$(id -u):$(id -g)" -e HOME=/tmp --label "mcp-stdio-repro=$RID")
M=(-v "$H:/src:ro" -v "$H/CONFIG.json:/cfg/CONFIG.json:ro" -v "$H/rerun/lists.sh:/lists.sh:ro")
BOUND=(--cpus "$CPUS" --memory "$MEM" --pids-limit "$PIDS")
LIM=(--network none "${BOUND[@]}")
BG=()

log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG" >&2; }
cleanup() {
  [ ${#BG[@]} -eq 0 ] || kill "${BG[@]}" 2>/dev/null || true
  ids=$(docker ps -aq --filter "label=mcp-stdio-repro=$RID" 2>/dev/null || true)
  [ -z "$ids" ] || { log "removing containers of this run: $(echo $ids)"; docker rm -f $ids >/dev/null 2>&1 || true; }
}
# A timed-out docker client usually ends 137 (killed after the grace period), so judge timeouts by elapsed time.
why() { [ "$2" -ge "$3" ] && echo "$1 (timeout after $2s)" || echo "$1"; }
fail() { echo "$*" >> "$W/out/INCOMPLETE"; log "INCOMPLETE: $*"; cleanup; exit 1; }
trap 'fail "interrupted"' INT TERM
trap 'rc=$?; [ $rc -eq 0 ] || [ -e "$W/out/INCOMPLETE" ] || echo "driver exited $rc" >> "$W/out/INCOMPLETE"; cleanup' EXIT
# step NAME SECONDS docker-run-args...: one bounded container, named so cleanup can find it.
step() {
  local n=$1 t=$2 s=$SECONDS rc=0; shift 2
  log "start $n (limit ${t}s)"
  # Run in the background and wait, so a signal to the driver is handled at once.
  timeout --kill-after=10 "$t" docker run --name "repro-$RID-$n" "${U[@]}" "$@" &
  BG=($!); wait "${BG[0]}" || rc=$?; BG=()
  log "end $n rc=$rc after $((SECONDS - s))s"
  [ $rc -eq 0 ] || fail "$n exited $(why $rc $((SECONDS - s)) $t)"
}

if [ "${SKIP_SETUP:-0}" != 1 ]; then
  # Networked (default bridge): PyPI, npm and the Go module proxy. Runs third-party install code, so bounded too.
  step setup-py-node "$SETUP_TIMEOUT" "${BOUND[@]}" "${M[@]}" -v "$W/envs:/envs" "$IMG" bash /src/rerun/setup-py-node.sh
  step setup-go "$SETUP_TIMEOUT" "${BOUND[@]}" "${M[@]}" -e GOCACHE=/envs/gocache -e GOMODCACHE=/envs/gomod \
    -v "$W/envs:/envs" -v "$W/scratch:/scratch" "$IMG" bash /src/rerun/setup-go.sh
fi

# Everything below runs offline, environments read-only.
step phase1 "$PHASE1_TIMEOUT" "${LIM[@]}" "${M[@]}" -v "$W/envs:/envs:ro" -v "$W/out/phase1:/out" "$IMG" bash /src/rerun/phase1.sh
ARMS=(go py ts aux)
log "start matrix: ${#ARMS[@]} containers at once (limit ${MATRIX_TIMEOUT}s each)"; s=$SECONDS
for p in "${ARMS[@]}"; do
  d=main-$p; [ $p = aux ] && d=aux
  timeout --kill-after=10 "$MATRIX_TIMEOUT" docker run --name "repro-$RID-$d" "${U[@]}" "${LIM[@]}" "${M[@]}" \
    -v "$W/envs:/envs:ro" -v "$W/out/$d:/out" "$IMG" bash /src/rerun/mainrun.sh $p > "$W/out/run-$p.log" 2>&1 &
  BG+=($!)
done
bad=()
for i in "${!ARMS[@]}"; do
  rc=0; wait "${BG[$i]}" || rc=$?
  log "end matrix ${ARMS[$i]} rc=$rc after $((SECONDS - s))s"
  [ $rc -eq 0 ] || bad+=("${ARMS[$i]} exited $(why $rc $((SECONDS - s)) $MATRIX_TIMEOUT)")
done
BG=()
[ ${#bad[@]} -eq 0 ] || fail "matrix: ${bad[*]}; see out/run-*.log"

# merge_results.py copies cells and tap logs only; analyze.py and posthoc_gap.py also need probes and client eras.
step merge "$MERGE_TIMEOUT" "${LIM[@]}" "${M[@]}" -v "$W/out:/out" "$IMG" bash -c '
  set -e
  python3 /src/merge_results.py /out/merged /out/phase1 /out/main-go /out/main-py /out/main-ts /out/aux
  cp -r /out/phase1/probes /out/phase1/client_era.json /out/merged/
  python3 /src/analyze.py /cfg/CONFIG.json /out/merged > /out/merged/RESULT.json
  python3 /src/posthoc_gap.py /out/merged > /out/merged/POSTHOC-gap.json'
log "done: $W/out/merged/RESULT.json"
