#!/bin/sh
# usage: run_all.sh OUTDIR ARM [ARM...]; skips completed outputs.
OUT=$1; shift
for ARM in "$@"; do for DOM in E W; do
 for M in SeasonalNaive AutoETS Timestral-5M Timestral-28M Timestral-209M Chronos-2-small Chronos-2 TimesFM-2.5 MSTL AutoARIMA; do
  [ -s "$OUT/$ARM/$DOM/$M.json" ] && continue
  [ "$DOM" = E ] && [ "$M" = AutoARIMA ] && continue
  [ "$DOM" = W ] && [ "$M" = MSTL ] && continue
  /opt/env/venv/bin/python -I /opt/src/run.py "$ARM" "$DOM" "$M" "$OUT" || echo "FAIL $ARM $DOM $M rc=$?"
 done; done; done
