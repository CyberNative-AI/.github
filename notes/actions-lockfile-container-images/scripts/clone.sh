#!/bin/bash
# clone.sh DEST OWNER/REPO : depth-1 partial clone with only .github/ checked out
set -u
DEST=$1 R=$2 D="$1/${2//\//__}"
[ -f "$D/.done" ] && exit 0
rm -rf "$D"
export GIT_TERMINAL_PROMPT=0 GIT_LFS_SKIP_SMUDGE=1
timeout 120 git clone -q --depth 1 --filter=blob:none --no-checkout --sparse "https://github.com/$R.git" "$D" 2>/dev/null || { echo "$R clone-fail"; exit 0; }
git -C "$D" sparse-checkout set --no-cone '/.github/' 2>/dev/null
timeout 120 git -C "$D" -c core.symlinks=false checkout -q 2>/dev/null || { echo "$R checkout-fail"; exit 0; }
git -C "$D" rev-parse HEAD > "$D/.head"; rm -rf "$D/.git"; touch "$D/.done"
