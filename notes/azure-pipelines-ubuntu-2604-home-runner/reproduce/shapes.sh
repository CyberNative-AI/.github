#!/bin/bash
# Run each usage shape with the agent home that $HOME points to (/home/vsts = old layout, /home/runner = Ubuntu 26.04 layout).
# usage: shapes.sh LAYOUT SET   (SET = base | py | node). One JSON line per shape on stdout.
LAYOUT=$1; SET=$2
export PATH="$HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
mkdir -p "$HOME/work/1/s" "$HOME/.local/bin"
printf '#!/bin/sh\necho mytool-ok\n' > "$HOME/.local/bin/mytool"; chmod +x "$HOME/.local/bin/mytool"
BUNDLED=$(ls -d /usr/local/lib/python3*/ensurepip/_bundled 2>/dev/null | head -1)

emit() { # shape rc effect errfile
  local err; err=$(grep -v '^\s*$' "$4" 2>/dev/null | head -2 | tr '\n' ' ' | sed 's/\\/\\\\/g; s/"/\\"/g' | cut -c1-220)
  printf '{"layout":"%s","set":"%s","shape":"%s","rc":%s,"effect":%s,"err":"%s"}\n' "$LAYOUT" "$SET" "$1" "$2" "$3" "$err"
}
run() { # shape effect-test -- command...
  local shape=$1 eff=$2; shift 3
  local e; e=$(mktemp); ( "$@" ) >"$e.out" 2>"$e"; local rc=$?
  if eval "$eff" >/dev/null 2>&1; then effect=true; else effect=false; fi
  emit "$shape" "$rc" "$effect" "$e"
}
P=/home/vsts   # the hard-coded literal under test
if [ "$SET" = base ]; then
  run S1 'true' -- bash -c "cd $P/work/1/s && pwd"
  run S2 'true' -- bash -c "export PATH=$P/.local/bin:\$PATH; mytool | grep -q mytool-ok"
  run S3 'true' -- bash -c "$P/.local/bin/mytool | grep -q mytool-ok"
  run S4 "test -d $P/.cache/x" -- bash -c "mkdir -p $P/.cache/x"
  run S5 'true' -- bash -c "ls $P/work/1/s"
  run S9 'true' -- bash -c "test -d $P/work && echo yes || echo no"
  run F1 'true' -- bash -c 'cd $HOME/work/1/s && pwd'
  run F3 'true' -- bash -c '$HOME/.local/bin/mytool | grep -q mytool-ok'
  run F4 'test -d $HOME/.cache/x' -- bash -c 'mkdir -p $HOME/.cache/x'
elif [ "$SET" = py ]; then
  rm -rf /tmp/t6 /tmp/v7 /tmp/tf6 /tmp/vf7
  run S6 'test -d /tmp/t6/pip' -- env PIP_CACHE_DIR=$P/.cache/pip python3 -m pip install --disable-pip-version-check --no-index --find-links "$BUNDLED" --target /tmp/t6 pip
  run S7 'test -d /tmp/v7/lib/python3.13/site-packages/pip' -- bash -c "export UV_CACHE_DIR=$P/.cache/uv; /opt/uv venv -q /tmp/v7 --python /usr/local/bin/python3 && /opt/uv pip install -q --offline --no-index --find-links $BUNDLED pip -p /tmp/v7"
  run F6 'test -d /tmp/tf6/pip' -- env PIP_CACHE_DIR=$HOME/.cache/pip python3 -m pip install --disable-pip-version-check --no-index --find-links "$BUNDLED" --target /tmp/tf6 pip
  run F7 'test -d /tmp/vf7/lib/python3.13/site-packages/pip' -- bash -c 'export UV_CACHE_DIR=$HOME/.cache/uv; /opt/uv venv -q /tmp/vf7 --python /usr/local/bin/python3 && /opt/uv pip install -q --offline --no-index --find-links '"$BUNDLED"' pip -p /tmp/vf7'
elif [ "$SET" = node ]; then
  for d in p8 pf8; do rm -rf /tmp/$d; mkdir -p /tmp/$d/dep /tmp/$d/app
    echo '{"name":"dep","version":"1.0.0"}' > /tmp/$d/dep/package.json
    echo '{"name":"app","version":"1.0.0","dependencies":{"dep":"file:../dep"}}' > /tmp/$d/app/package.json; done
  run S8 'test -e /tmp/p8/app/node_modules/dep' -- bash -c "cd /tmp/p8/app && npm_config_cache=$P/.npm npm install --offline --no-audit --no-fund"
  for d in p8b pf8b; do rm -rf /tmp/$d; mkdir -p /tmp/$d/dep /tmp/$d/app
    echo '{"name":"dep","version":"1.0.0"}' > /tmp/$d/dep/package.json
    (cd /tmp/$d && npm_config_cache=/tmp/$d/c0 npm pack ./dep --silent >/dev/null 2>&1)
    echo '{"name":"app","version":"1.0.0","dependencies":{"dep":"file:../dep-1.0.0.tgz"}}' > /tmp/$d/app/package.json; done
  run S8b 'test -e /tmp/p8b/app/node_modules/dep/package.json' -- bash -c "cd /tmp/p8b/app && npm_config_cache=$P/.npm npm install --offline --no-audit --no-fund"
  run F8b 'test -e /tmp/pf8b/app/node_modules/dep/package.json' -- bash -c 'cd /tmp/pf8b/app && npm_config_cache=$HOME/.npm npm install --offline --no-audit --no-fund && test -d $HOME/.npm/_cacache'
  run F8 'test -e /tmp/pf8/app/node_modules/dep' -- bash -c 'cd /tmp/pf8/app && npm_config_cache=$HOME/.npm npm install --offline --no-audit --no-fund'
fi
