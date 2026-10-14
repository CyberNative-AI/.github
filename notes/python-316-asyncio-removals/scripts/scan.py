"""Scan latest PyPI release files of top-N packages for asyncio APIs removed in 3.16.0a1.
Usage: python3 -I scan.py top.json N dl_dir out.jsonl"""
import json, sys, re, zipfile, tarfile, io, urllib.request, concurrent.futures as cf, os
top, N, dl, outp = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
PAT = re.compile(rb'(set_event_loop_policy|get_event_loop_policy|DefaultEventLoopPolicy|AbstractEventLoopPolicy|WindowsSelectorEventLoopPolicy|WindowsProactorEventLoopPolicy|asyncio\.iscoroutinefunction|asyncio\.coroutines\.iscoroutinefunction)')
rows = json.load(open(top))['rows'][:N]
def pick(files):
    whl = [f for f in files if f['packagetype'] == 'bdist_wheel' and not f.get('yanked')]
    for pref in ('-none-any.whl', 'manylinux', 'linux_x86_64', ''):
        c = [f for f in whl if pref in f['filename'] and ('x86_64' in f['filename'] or 'any' in f['filename'] or pref == '')]
        if c: return sorted(c, key=lambda f: f['filename'])[-1]
    sd = [f for f in files if f['packagetype'] == 'sdist']
    return sd[0] if sd else None
def one(r):
    name = r['project']
    try:
        meta = json.load(urllib.request.urlopen(f'https://pypi.org/pypi/{name}/json', timeout=60))
        ver = meta['info']['version']; f = pick(meta['urls'])
        if not f: return dict(name=name, version=ver, err='nofile')
        data = urllib.request.urlopen(f['url'], timeout=120).read()
        hits = {}
        def scan(path, b):
            if not path.endswith(('.py', '.pyi', '.pyx')): return
            for i, line in enumerate(b.splitlines(), 1):
                m = PAT.search(line)
                if m: hits.setdefault(path, []).append([i, m.group(1).decode(), line.strip()[:200].decode('utf-8', 'replace')])
        if f['filename'].endswith('.whl') or f['filename'].endswith('.zip'):
            z = zipfile.ZipFile(io.BytesIO(data))
            for n in z.namelist(): scan(n, z.read(n)) if n.endswith(('.py', '.pyi', '.pyx')) else None
        else:
            t = tarfile.open(fileobj=io.BytesIO(data))
            for m in t.getmembers():
                if m.isfile() and m.name.endswith(('.py', '.pyi', '.pyx')): scan(m.name, t.extractfile(m).read())
        return dict(name=name, version=ver, file=f['filename'], sha256=f['digests']['sha256'], upload=f.get('upload_time_iso_8601'), requires_python=meta['info'].get('requires_python'), hits=hits)
    except Exception as e:
        return dict(name=name, err=repr(e)[:200])
with open(outp, 'w') as o, cf.ThreadPoolExecutor(16) as ex:
    for res in ex.map(one, rows):
        o.write(json.dumps(res) + '\n'); o.flush()
