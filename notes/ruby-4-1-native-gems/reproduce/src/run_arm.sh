#!/bin/bash
# inside container: ARM env; /gems ro, /src ro, /work rw
set -u
export OUT=/work/$ARM; mkdir -p "$OUT/res"
ruby -v >"$OUT/ruby-v.txt"; gem -v >>"$OUT/ruby-v.txt"; gcc --version | head -1 >>"$OUT/ruby-v.txt"
# controls first (built from gemspec inside container)
mkdir -p "$OUT/ctl"; for c in cyba_untyped cyba_typed; do cp -r /src/controls/$c "$OUT/ctl/"; (cd "$OUT/ctl/$c" && gem build $c.gemspec -o "$OUT/ctl/$c-0.0.1.gem" >/dev/null 2>&1); done
ls "$OUT"/ctl/*.gem | xargs -n1 -P2 bash /src/src/run_one.sh
ls /gems/*.gem | sort | xargs -n1 -P4 bash /src/src/run_one.sh
echo DONE >"$OUT/DONE"
