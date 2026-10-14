"""Run each documented replacement on the current interpreter.
Usage: python fixes.py TGTDIR  -> JSON lines: fix, rc, out, err (last stderr line).
Each case runs in a fresh subprocess with PYTHONPATH set to the named package dirs."""
import json, subprocess, sys

tgt = sys.argv[1]
SHIM = (
    "import asyncio, inspect\n"
    "if not hasattr(asyncio, 'iscoroutinefunction'):\n"
    "    asyncio.iscoroutinefunction = inspect.iscoroutinefunction\n"
)
CASES = {
    # backoff 2.2.1: shim restores the removed name before import
    'backoff + iscoroutinefunction shim (sync+async)': (['backoff'], SHIM +
        "import backoff\n"
        "@backoff.on_exception(backoff.constant, ValueError, max_tries=3, interval=0)\n"
        "def f(n=[0]):\n    n[0] += 1\n    if n[0] < 3: raise ValueError\n    return n[0]\n"
        "@backoff.on_predicate(backoff.constant, max_tries=3, interval=0)\n"
        "async def g(n=[0]):\n    n[0] += 1\n    return n[0] >= 2\n"
        "print(f(), asyncio.run(g()))"),
    # tenacity: maintained alternative, no shim
    'tenacity retry (sync+async)': (['tenacity'],
        "import asyncio\nfrom tenacity import retry, stop_after_attempt, retry_if_result\n"
        "@retry(stop=stop_after_attempt(3))\n"
        "def f(n=[0]):\n    n[0] += 1\n    if n[0] < 3: raise ValueError\n    return n[0]\n"
        "@retry(stop=stop_after_attempt(3), retry=retry_if_result(lambda r: not r))\n"
        "async def g(n=[0]):\n    n[0] += 1\n    return n[0] >= 2\n"
        "print(f(), asyncio.run(g()))"),
    # cached-property 2.0.1: shim; and stdlib functools.cached_property for sync use
    'cached-property + shim (sync+async)': (['cached-property'], SHIM +
        "from cached_property import cached_property\n"
        "class A:\n    @cached_property\n    def v(self): return 1\n"
        "    @cached_property\n    async def w(self): return 2\n"
        "a = A()\n"
        "async def main(): return await a.w, await a.w\n"
        "print(a.v, asyncio.run(main()))"),
    'functools.cached_property (sync)': ([],
        "from functools import cached_property\n"
        "class A:\n    @cached_property\n    def v(self): return 1\nprint(A().v)"),
    # mock 5.2.0: use the stdlib module instead
    'unittest.mock incl. AsyncMock': ([],
        "import asyncio\nfrom unittest import mock\n"
        "m = mock.AsyncMock(return_value=3)\nprint(asyncio.run(m()), mock.MagicMock()(1) is not None)"),
    # nest-asyncio 1.6.0 -> nest-asyncio2 (maintained fork)
    'nest-asyncio2 nested run': (['nest-asyncio2'],
        "import asyncio, nest_asyncio2\nnest_asyncio2.apply()\n"
        "async def inner(): return 1\n"
        "async def outer(): return asyncio.run(inner()) + 1\nprint(asyncio.run(outer()))"),
    # set_event_loop_policy(...) users: pass a loop factory instead
    'asyncio.run(loop_factory=SelectorEventLoop)': ([],
        "import asyncio\n"
        "async def m(): return type(asyncio.get_running_loop()).__name__\n"
        "print(asyncio.run(m(), loop_factory=asyncio.SelectorEventLoop))"),
    'asyncio.Runner(loop_factory=...)': ([],
        "import asyncio\n"
        "async def m(): return 1\n"
        "with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as r:\n    print(r.run(m()), r.run(m()))"),
    # tornado AnyThreadEventLoopPolicy users: give each thread its own loop
    'tornado IOLoop in a worker thread': (['tornado'],
        "import asyncio, threading\nfrom tornado.ioloop import IOLoop\nres = []\n"
        "def worker():\n    asyncio.set_event_loop(asyncio.new_event_loop())\n"
        "    async def m(): return 7\n    res.append(IOLoop.current().run_sync(m))\n"
        "t = threading.Thread(target=worker); t.start(); t.join(); print(res)"),
    'inspect.iscoroutinefunction + markcoroutinefunction': ([],
        "import inspect, functools\n"
        "async def a(): pass\n"
        "def wrap(f):\n    @functools.wraps(f)\n    def w(*x): return f(*x)\n    return inspect.markcoroutinefunction(w)\n"
        "print(inspect.iscoroutinefunction(a), inspect.iscoroutinefunction(wrap(a)))"),
}
for name, (pkgs, code) in CASES.items():
    env = {'PYTHONPATH': ':'.join(f'{tgt}/{p}' for p in pkgs), 'PYTHONDONTWRITEBYTECODE': '1'}
    r = subprocess.run([sys.executable, '-W', 'error::DeprecationWarning', '-c', code],
                       capture_output=True, text=True, timeout=120, env=env, cwd='/tmp')
    print(json.dumps(dict(py=sys.version.split()[0], fix=name, rc=r.returncode,
                          out=r.stdout.strip()[-120:],
                          err=(r.stderr.strip().splitlines() or [''])[-1][:200])))
