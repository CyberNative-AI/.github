#!/bin/bash
# clone.sh DEST OWNER/REPO : depth-1 partial clone of the default branch with only the workflows
# and the version files setup-beam reads checked out; records the last commit date in .head-date
set -u
DEST=$1 R=$2 D="$1/${2//\//__}"
[ -f "$D/.done" ] && exit 0
rm -rf "$D"
export GIT_TERMINAL_PROMPT=0 GIT_LFS_SKIP_SMUDGE=1
timeout 120 git clone -q --depth 1 --filter=blob:none --no-checkout --sparse "https://github.com/$R.git" "$D" 2>/dev/null || { echo "$R clone-fail"; exit 0; }
git -C "$D" sparse-checkout set --no-cone '/.github/workflows/' '/.tool-versions' '/mise.toml' '/.mise.toml' 2>/dev/null
timeout 120 git -C "$D" -c core.symlinks=true checkout -q 2>/dev/null || { echo "$R checkout-fail"; exit 0; }
git -C "$D" log -1 --format=%cs > "$D/.head-date"
rm -rf "$D/.git/objects/pack"; touch "$D/.done"
