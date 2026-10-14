"""Call-time probes per package target. Usage: python probes2.py tgtdir"""
import subprocess, sys, json
tgt = sys.argv[1]
P = {
 'mock': "import mock; print(mock.__version__)",
 'fire': "import fire\ndef hello(name='x'): return 'hi '+name\nfire.Fire(hello, command=['--name','y'])",
 'cached-property': "from cached_property import cached_property\nclass A:\n    @cached_property\n    def v(self): return 1\nprint(A().v)",
 'fastcore': "from fastcore.xtras import *\nimport fastcore.xtras as X\nprint([n for n in dir(X) if 'async' in n.lower()][:5])",
 'respx': "import respx.fixtures; print('ok')",
 'posthog': "import posthog; print('ok')",
 'backoff': "import backoff\n@backoff.on_exception(backoff.expo, ValueError, max_tries=1)\ndef f(): return 1\nprint(f())",
 'nest-asyncio': "import nest_asyncio; nest_asyncio.apply(); print('ok')",
 'nest-asyncio2': "import nest_asyncio2; nest_asyncio2.apply(); print('ok')",
 'freezegun': "import asyncio\nfrom freezegun import freeze_time\n@freeze_time('2020-01-01')\nasync def m():\n    import datetime; return datetime.date.today()\nprint(asyncio.run(m()))",
}
for n, code in P.items():
    r = subprocess.run([sys.executable, '-c', 'import warnings; warnings.simplefilter("ignore")\n' + code], capture_output=True, text=True, timeout=120, env={'PYTHONPATH': f'{tgt}/{n}', 'PYTHONDONTWRITEBYTECODE': '1'})
    print(json.dumps(dict(pkg=n, rc=r.returncode, out=r.stdout.strip()[-120:], err=(r.stderr.strip().splitlines() or [''])[-1][:200])))
