"""Download each frame gem's latest ruby-platform .gem; read metadata.gz `extensions:`; keep native .gem files on bulk."""
import json, gzip, io, re, tarfile, time, urllib.request, urllib.parse, concurrent.futures as cf, pathlib, sys
UA = "cybernative-research/1.0 (+hello@cybernative.ai)"
GEMS = pathlib.Path("gems")
def fetch(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(3 * (i + 1))
        except Exception:
            time.sleep(3 * (i + 1))
    return "ERR"
def exts_from_meta(y):
    m = re.search(r"^extensions:\s*(\[\])?\n((?:- .*\n)*)", y, re.M)
    if not m: return []
    return [l[2:].strip().strip("'\"") for l in m.group(2).splitlines()]
def one(r):
    if r.get("error") or not r.get("ruby_platform"): return {"name": r["name"], "native_status": "no_ruby_platform" if not r.get("error") else "frame_error"}
    fn = f"{r['name']}-{r['latest']}.gem"
    b = fetch(f"https://rubygems.org/gems/{urllib.parse.quote(fn)}")
    if b in (None, "ERR"): return {"name": r["name"], "native_status": "download_error"}
    try:
        with tarfile.open(fileobj=io.BytesIO(b)) as t:
            y = gzip.decompress(t.extractfile("metadata.gz").read()).decode("utf-8", "replace")
    except Exception as e:
        return {"name": r["name"], "native_status": f"parse_error:{type(e).__name__}"}
    ex = exts_from_meta(y)
    rv = re.search(r"^required_ruby_version: !ruby/object:Gem::Requirement\n  requirements:\n((?:  - .*\n(?:    .*\n)*)*)", y, re.M)
    if ex: (GEMS / fn).write_bytes(b)
    return {"name": r["name"], "native_status": "native" if ex else "pure", "extensions": ex, "gem_bytes": len(b)}
if __name__ == "__main__":
    rows = [json.loads(l) for l in open("data/frame.jsonl")]
    with cf.ThreadPoolExecutor(8) as ex: res = list(ex.map(one, rows))
    with open("data/native.jsonl", "w") as f:
        for r in res: f.write(json.dumps(r) + "\n")
    from collections import Counter
    print(Counter(r["native_status"] for r in res))
