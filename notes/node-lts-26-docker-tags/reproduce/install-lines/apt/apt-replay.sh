#!/bin/sh
# Debian package-list replay: /in/lists-$VARIANT.txt = one apt package list per line ("<id>\t<pkgs>"); simulate install, no downloads.
set -u
O=/work/apt-$TAG.tsv; : >"$O"
apt-get update -qq >/work/apt-$TAG.update.log 2>&1; echo "update_rc=$?" >/work/apt-$TAG.meta
date -u +%FT%TZ >>/work/apt-$TAG.meta
while IFS="$(printf '\t')" read -r id pkgs; do
  out=$(DEBIAN_FRONTEND=noninteractive apt-get install -s -y --no-install-recommends $pkgs 2>&1); rc=$?
  err=$(printf '%s' "$out" | grep -E '^(E:|Package .* is|  .*but it is not|Package .* has no installation)' | head -3 | tr '\n\t' '  ')
  printf '%s\t%s\t%s\n' "$id" "$rc" "$err" >>"$O"
done </in/lists-$VARIANT.txt
echo DONE >>/work/apt-$TAG.meta
