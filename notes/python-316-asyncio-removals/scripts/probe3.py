"""Same-bytes probes run under each interpreter. Usage: python probe3.py tgtdir"""
import sys, subprocess, json
t = sys.argv[1]
cases = {
 'pytest-asyncio': ([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '/probe/t_async.py'], 'pytest-asyncio'),
 'posthog.integrations.django': ([sys.executable, '-c', 'import posthog.integrations.django'], 'posthog'),
 'tornado AnyThreadEventLoopPolicy': ([sys.executable, '-W', 'ignore', '-c', 'from tornado.platform.asyncio import AnyThreadEventLoopPolicy'], 'tornado'),
}
for n, (cmd, d) in cases.items():
    r = subprocess.run(cmd, capture_output=True, text=True, env={'PYTHONPATH': f'{t}/{d}', 'PYTHONDONTWRITEBYTECODE': '1'}, cwd='/tmp')
    tail = (r.stdout.strip().splitlines() or [''])[-1] if 'pytest' in n else (r.stderr.strip().splitlines() or [''])[-1]
    print(json.dumps(dict(py=sys.version.split()[0], probe=n, rc=r.returncode, tail=tail[:160])))
