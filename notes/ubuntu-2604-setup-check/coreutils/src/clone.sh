#!/bin/bash
# usage: clone.sh owner/repo  -> repos/owner__repo/.github/workflows (sparse, depth 1, blobless)
r="$1"; d="repos/${r/\//__}"
[ -e "$d/.done" ] && exit 0
rm -rf "$d"
GIT_TERMINAL_PROMPT=0 timeout -k 5 90 git clone -q --depth 1 --filter=blob:none --no-checkout "https://github.com/$r.git" "$d" 2>/dev/null || { echo "$r CLONE_FAIL" >> clone-fail.log; exit 0; }
cd "$d" && git sparse-checkout set --no-cone '/.github/workflows/*' >/dev/null 2>&1 && timeout -k 5 90 git checkout -q 2>/dev/null; git rev-parse HEAD > .head 2>/dev/null; touch .done
