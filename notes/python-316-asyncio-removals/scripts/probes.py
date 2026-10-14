"""Runtime probes on CPython 3.16.0a1 (Linux). Each probe runs in a fresh subprocess.
Usage: python probes.py  -> JSON lines: name, ok, error (last line of traceback)."""
import subprocess, sys, json
P = {
 'backoff.on_exception (sync fn)': "import backoff\n@backoff.on_exception(backoff.expo, ValueError, max_tries=1)\ndef f(): return 1\nprint(f())",
 'backoff.on_predicate (async fn)': "import backoff, asyncio\n@backoff.on_predicate(backoff.constant, max_tries=1)\nasync def f(): return 1\nprint(asyncio.run(f()))",
 'nest_asyncio.apply()': "import nest_asyncio, asyncio\nnest_asyncio.apply()\nasync def g(): return 1\nprint(asyncio.run(g()))",
 'uvloop absent check': "import importlib.util;print(importlib.util.find_spec('uvloop') is not None)",
 'pytest-asyncio trivial test': None,
 'anyio.run': "import anyio\nasync def m(): await anyio.sleep(0); return 1\nprint(anyio.run(m))",
 'tornado IOLoop run_sync': "from tornado.ioloop import IOLoop\nasync def m(): return 1\nprint(IOLoop.current().run_sync(m))",
 'tornado AnyThreadEventLoopPolicy': "from tornado.platform.asyncio import AnyThreadEventLoopPolicy\nprint(AnyThreadEventLoopPolicy)",
 'aiohttp web app': "import asyncio\nfrom aiohttp import web\nasync def h(r): return web.Response(text='ok')\napp=web.Application(); app.router.add_get('/',h)\nprint('ok')",
 'psycopg import': "import psycopg; print(psycopg.__version__)",
 'sqlalchemy.ext.asyncio import': "import sqlalchemy.ext.asyncio; print('ok')",
 'starlette/fastapi app': "from fastapi import FastAPI\nfrom fastapi.testclient import TestClient\napp=FastAPI()\n@app.get('/')\nasync def r(): return {'a':1}\nprint(TestClient(app).get('/').json())",
 'asgiref sync_to_async': "import asyncio\nfrom asgiref.sync import sync_to_async\nprint(asyncio.run(sync_to_async(lambda: 1)()))",
 'redis.asyncio import': "import redis.asyncio; print('ok')",
 'jupyter_core run_sync': "from jupyter_core.utils import run_sync\nasync def m(): return 1\nprint(run_sync(m)())",
 'zmq.asyncio import': "import zmq.asyncio; print('ok')",
 'sentry_sdk init': "import sentry_sdk; sentry_sdk.init(); print('ok')",
}
for name, code in P.items():
    if code is None:
        cmd = [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '/probe/t_async.py']
    else:
        cmd = [sys.executable, '-c', code]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    err = (r.stderr.strip().splitlines() or [''])[-1] if r.returncode else ''
    if code is None and r.returncode: err = [l for l in r.stdout.splitlines() if 'Error' in l][-1:] or r.stdout.strip().splitlines()[-1:]
    print(json.dumps(dict(name=name, rc=r.returncode, out=r.stdout.strip()[-200:] if not r.returncode else '', err=err)))
