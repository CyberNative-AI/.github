"""Census source scan. Shallow, blob-limited, no-checkout clones; reads only locally present blobs."""
import json, os, re, subprocess, sys, hashlib
from concurrent.futures import ThreadPoolExecutor
frame = json.load(open(sys.argv[1])); repos = sys.argv[2]; out = sys.argv[3]; workers = int(sys.argv[4]) if len(sys.argv) > 4 else 6
BP = re.compile(r'(override\s+fun|void)\s+onBackPressed\s*\(')
BK = re.compile(r'KEYCODE_BACK')
OPTF = re.compile(r'enableOnBackInvokedCallback\s*=\s*"false"')
OPTT = re.compile(r'enableOnBackInvokedCallback\s*=\s*"true"')
HT = re.compile(r'targetSdk(Version)?\s*[=(:]?\s*(\d+)')
HTQ = re.compile(r'targetSdk(Version)?\w*\s*[=(:]?\s*["\']?(\d+)')  # descriptive sensitivity only (quote-tolerant)
TESTP = re.compile(r'(^|/)(test|androidTest|src/test[^/]*)(/|$)')
env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_ASKPASS="/bin/false")
def git(d, *a, inp=None, timeout=600):
    return subprocess.run(["git", "-C", d, *a], input=inp, capture_output=True, timeout=timeout, env=env)
def comment(l):
    s = l.strip(); return s.startswith("//") or s.startswith("*") or s.startswith("/*") or s.startswith("<!--")
def one(r):
    name = hashlib.sha1(r["source"].encode()).hexdigest()[:12]; d = os.path.join(repos, name)
    res = {"pkg": r["pkg"], "source": r["source"], "dir": name}
    try:
        if not os.path.isdir(os.path.join(d, ".git")) and not os.path.exists(os.path.join(d, "HEAD")):
            p = subprocess.run(["git", "clone", "-q", "--depth", "1", "--filter=blob:limit=2m", "--no-checkout",
                                r["source"] + ("" if r["source"].endswith(".git") else ".git"), d],
                               capture_output=True, timeout=900, env=env)
            if p.returncode != 0:
                res["error"] = "clone:" + p.stderr.decode(errors="replace")[-200:]; return res
        head = git(d, "rev-parse", "HEAD").stdout.decode().strip(); res["head"] = head
        res["commit_date"] = git(d, "log", "-1", "--format=%cI").stdout.decode().strip()
        local = set(l.split()[0] for l in git(d, "cat-file", "--batch-all-objects", "--batch-check=%(objectname) %(objecttype)").stdout.decode().splitlines() if l.endswith(" blob"))
        want = []
        for l in git(d, "ls-tree", "-r", "-z", "HEAD").stdout.decode(errors="replace").split("\0"):
            if not l: continue
            meta, path = l.split("\t", 1); mode, typ, oid = meta.split()
            if typ != "blob" or "node_modules/" in path: continue
            base = path.rsplit("/", 1)[-1]
            if path.endswith((".java", ".kt")) or base in ("AndroidManifest.xml", "package.json", "pubspec.yaml", "config.xml", "libs.versions.toml") or base.endswith((".gradle", ".gradle.kts")):
                want.append((path, oid))
        res["files_wanted"] = len(want); present = [(p, o) for p, o in want if o in local]; res["files_read"] = len(present)
        bp, bk, optf, optt, ht, htq, fw = [], [], [], [], [], [], {}
        if present:
            blob = git(d, "cat-file", "--batch", inp="\n".join(o for _, o in present).encode() + b"\n").stdout
            pos = 0; texts = []
            for p, o in present:
                nl = blob.index(b"\n", pos); hdr = blob[pos:nl].split(); size = int(hdr[2])
                texts.append((p, blob[nl+1:nl+1+size].decode(errors="replace"))); pos = nl + 1 + size + 1
            for p, t in texts:
                test = bool(TESTP.search(p)); base = p.rsplit("/", 1)[-1]
                if p.endswith((".java", ".kt")) and not test:
                    for i, l in enumerate(t.splitlines(), 1):
                        if comment(l): continue
                        if BP.search(l): bp.append(f"{p}:{i}")
                        if BK.search(l): bk.append(f"{p}:{i}")
                if base == "AndroidManifest.xml" and not test:
                    for i, l in enumerate(t.splitlines(), 1):
                        if comment(l): continue
                        if OPTF.search(l): optf.append(f"{p}:{i}")
                        if OPTT.search(l): optt.append(f"{p}:{i}")
                if base.endswith((".gradle", ".gradle.kts")) or base == "libs.versions.toml":
                    for l in t.splitlines():
                        if comment(l): continue
                        ht += [int(m.group(2)) for m in HT.finditer(l)]; htq += [int(m.group(2)) for m in HTQ.finditer(l)]
                if base == "package.json":
                    try: j = json.loads(t)
                    except Exception: j = {}
                    deps = {**(j.get("dependencies") or {}), **(j.get("devDependencies") or {})} if isinstance(j, dict) else {}
                    for k in ("cordova-android", "react-native", "@capacitor/android"):
                        if k in deps and isinstance(deps[k], str): fw.setdefault(k, deps[k])
                if base == "config.xml" and "<widget" in t: fw.setdefault("cordova_config", p)
                if base == "pubspec.yaml" and re.search(r'^\s*sdk:\s*flutter', t, re.M): fw.setdefault("flutter", p)
        res.update(bp=bp, bk=bk, optf=optf, optt=optt, head_target=max(ht) if ht else None,
                   head_target_q=max(htq) if htq else None, fw=fw)
    except Exception as e:
        res["error"] = "scan:" + type(e).__name__ + ":" + str(e)[:150]
    return res
done = {json.loads(l)["pkg"] for l in open(out)} if os.path.exists(out) else set()
todo = [r for r in frame if r["pkg"] not in done]
with open(out, "a") as f, ThreadPoolExecutor(workers) as ex:
    for res in ex.map(one, todo):
        f.write(json.dumps(res) + "\n"); f.flush()
print("done", len(todo))
