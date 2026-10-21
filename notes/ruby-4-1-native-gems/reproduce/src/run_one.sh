#!/bin/bash
# usage: run_one.sh <gemfile path>   env: ARM, OUT (/work/<arm>)
g="$1"; base=$(basename "$g" .gem); name="${base%-*}"
d="$OUT/res/$base"; rm -rf "$d"; mkdir -p "$d"
export GEM_HOME="$OUT/gh/$base" GEM_PATH="$OUT/gh/$base" TMPDIR="$OUT/tmp/$base" MAKEFLAGS=-j2
mkdir -p "$GEM_HOME" "$TMPDIR"
start=$(date +%s)
timeout -k 10 900 gem install --no-document "$g" >"$d/install.log" 2>&1; echo $? >"$d/install.rc"
echo $(( $(date +%s) - start )) >"$d/install.secs"
# load attempts: name, name with - -> /, name with - -> _
: >"$d/load.tsv"
for req in "$name" "${name//-//}" "${name//-/_}"; do
  out=$(cd /tmp && timeout -k 5 120 ruby -e "gem '$name'; require '$req'; puts 'LOADED'" 2>&1 | tail -c 600 | tr '\n\t' '  ')
  printf '%s\t%s\n' "$req" "$out" >>"$d/load.tsv"
done
# undefined symbols of the target gem's own shared objects
find "$GEM_HOME/extensions" "$GEM_HOME/gems/$base" -name '*.so' 2>/dev/null | sort -u >"$d/so.list"
: >"$d/undef.txt"
while read -r so; do nm -D --undefined-only "$so" 2>/dev/null | awk '{print $NF}' | sed "s|^|$(basename "$so")\t|" >>"$d/undef.txt"; done <"$d/so.list"
rm -rf "$GEM_HOME" "$TMPDIR"
