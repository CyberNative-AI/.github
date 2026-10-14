#!/bin/sh
# Does running on 3.15 with DeprecationWarning as error catch each 3.16 break?
# Usage: warn315.sh PYTHON315 TGTDIR PLAIN_TEST_DIR
P=$1; T=$2; D=$3
run() { n=$1; pk=$2; shift 2; out=$(cd /tmp && PYTHONPATH=$T/$pk PYTHONDONTWRITEBYTECODE=1 "$P" -W error::DeprecationWarning "$@" 2>&1); rc=$?; printf '%s\trc=%s\t%s\n' "$n" "$rc" "$(printf '%s' "$out" | tail -1 | cut -c1-140)"; }
run mock mock -c "import mock"
run cached-property cached-property -c "from cached_property import cached_property
class A:
    @cached_property
    def v(self): return 1
print(A().v)"
run backoff backoff -c "import backoff
@backoff.on_exception(backoff.expo, ValueError, max_tries=1)
def f(): return 1
print(f())"
run nest-asyncio nest-asyncio -c "import nest_asyncio; nest_asyncio.apply()"
run tornado-AnyThreadEventLoopPolicy tornado -c "from tornado.platform.asyncio import AnyThreadEventLoopPolicy"
out=$(cd "$D" && PYTHONPATH=$T/pytest-asyncio PYTHONDONTWRITEBYTECODE=1 "$P" -m pytest -p no:cacheprovider -q -W error::DeprecationWarning 2>&1); rc=$?
printf 'pytest-asyncio plain sync test\trc=%s\t%s\n' "$rc" "$(printf '%s' "$out" | tail -1)"
