#!/bin/sh
# Inside-container driver. usage: run_all.sh <reps> PAGE...   (OUT=/out)
set -u
R=$1; shift
cd /tmp
C156=/bin-cft/156.0.8078.47/chrome-linux64/chrome; C157=/bin-cft/157.0.8103.15/chrome-linux64/chrome; C158=/bin-cft/158.0.8119.0/chrome-linux64/chrome
ARMS=${ARMS:-"C156 C156OT C157 C158"}
for a in $ARMS; do
  case $a in
    C156) B=$C156; X="";;
    C156OT) B=$C156; X="--enable-blink-features=CanvasDrawElement";;
    C157) B=$C157; X="";;
    C158) B=$C158; X="";;
  esac
  EXTRA_FLAGS="$X" node /work/src/run.mjs $B $a /work/pages /assets /out $R "$@"
done
echo "done $(date -u +%FT%TZ)"
