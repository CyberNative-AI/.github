"""Depth-1 clones (blobs up to 2 MB, no checkout) of the frame rows; reads only local blobs as text and runs nothing from the repositories.
usage: census.py ROWS_JSON REPOS_DIR OUT_JSONL SUBSET(onplay|all) [workers]"""
import json, os, re, subprocess, sys, hashlib
from concurrent.futures import ThreadPoolExecutor
rows = json.load(open(sys.argv[1]))["rows"] if sys.argv[1].endswith("census-BP.json") else json.load(open(sys.argv[1]))
repos, out, subset = sys.argv[2], sys.argv[3], sys.argv[4]; workers = int(sys.argv[5]) if len(sys.argv) > 5 else 6
if subset == "onplay": rows = [r for r in rows if r.get("play") == "ON_PLAY"]
LOCKS = "portrait|reversePortrait|sensorPortrait|userPortrait|landscape|reverseLandscape|sensorLandscape|userLandscape"
CLOCK = "PORTRAIT|REVERSE_PORTRAIT|SENSOR_PORTRAIT|USER_PORTRAIT|LANDSCAPE|REVERSE_LANDSCAPE|SENSOR_LANDSCAPE|USER_LANDSCAPE"
RX = {
 "E":      (re.compile(r'name\s*=\s*"(android:)?windowOptOutEdgeToEdgeEnforcement"[^>]*>\s*true\s*<'), "resxml"),
 "O_MAN":  (re.compile(r'screenOrientation\s*=\s*"(%s)"' % LOCKS), "manifest"),
 "R_MAN":  (re.compile(r'resizeableActivity\s*=\s*"false"|(max|min)AspectRatio\s*='), "manifest"),
 "OPT_R":  (re.compile(r'PROPERTY_COMPAT_ALLOW_RESTRICTED_RESIZABILITY'), "manifest"),
 "GAME":   (re.compile(r'appCategory\s*=\s*"game"'), "manifest"),
 "O_CODE": (re.compile(r'(setRequestedOrientation\s*\(|requestedOrientation\s*=)\s*(android\.content\.pm\.)?(ActivityInfo\.)?SCREEN_ORIENTATION_(%s)\b' % CLOCK), "code"),
 "O_DART": (re.compile(r'setPreferredOrientations\s*\('), "dart"),
 "O_CDV":  (re.compile(r'<preference\s+name\s*=\s*"[Oo]rientation"\s+value\s*=\s*"(portrait|landscape)"'), "cdvconfig"),
 "O_EXPO": (re.compile(r'"orientation"\s*:\s*"(portrait|landscape)"'), "expo"),
}
HT = re.compile(r'targetSdk(Version)?\s*[=(:]?\s*(\d+)')
TESTP = re.compile(r'(^|/)(test|androidTest|src/test[^/]*)(/|$)')
env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_ASKPASS="/bin/false")
def git(d, *a, inp=None, timeout=600):
    return subprocess.run(["git", "-C", d, *a], input=inp, capture_output=True, timeout=timeout, env=env)
def comment(l):
    s = l.strip(); return s.startswith(("//", "*", "/*", "<!--", "#"))
def kind(path):
    base = path.rsplit("/", 1)[-1]
    if base == "AndroidManifest.xml": return "manifest"
    if re.search(r'(^|/)res/values[^/]*/[^/]+\.xml$', path): return "resxml"
    if path.endswith((".java", ".kt")): return "code"
    if path.endswith(".dart"): return "dart"
    if base == "config.xml": return "cdvconfig"
    if base in ("app.json", "app.config.json"): return "expo"
    if base.endswith((".gradle", ".gradle.kts")) or base == "libs.versions.toml": return "gradle"
    return None
def one(r):
    name = hashlib.sha1(r["source"].encode()).hexdigest()[:12]; d = os.path.join(repos, name)
    res = {"pkg": r["pkg"], "source": r["source"], "dir": name, "play": r.get("play"), "fdroid_target": r.get("fdroid_target")}
    try:
        if not os.path.exists(os.path.join(d, "HEAD")) and not os.path.isdir(os.path.join(d, ".git")):
            if subset == "all": res["error"] = "noclone"; return res  # read-only pass over existing clones
            p = subprocess.run(["git", "clone", "-q", "--depth", "1", "--filter=blob:limit=2m", "--no-checkout",
                                r["source"] + ("" if r["source"].endswith(".git") else ".git"), d], capture_output=True, timeout=900, env=env)
            if p.returncode != 0: res["error"] = "clone:" + p.stderr.decode(errors="replace")[-200:]; return res
        res["head"] = git(d, "rev-parse", "HEAD").stdout.decode().strip()
        res["commit_date"] = git(d, "log", "-1", "--format=%cI").stdout.decode().strip()
        local = set(l.split()[0] for l in git(d, "cat-file", "--batch-all-objects", "--batch-check=%(objectname) %(objecttype)").stdout.decode().splitlines() if l.endswith(" blob"))
        want = []
        for l in git(d, "ls-tree", "-r", "-z", "HEAD").stdout.decode(errors="replace").split("\0"):
            if not l: continue
            meta, path = l.split("\t", 1); mode, typ, oid = meta.split()
            if typ != "blob" or "node_modules/" in path or TESTP.search(path): continue
            k = kind(path)
            if k: want.append((path, oid, k))
        present = [w for w in want if w[1] in local]; res["files_wanted"] = len(want); res["files_read"] = len(present)
        hits = {k: [] for k in RX}; ht = []
        if present:
            blob = git(d, "cat-file", "--batch", inp="\n".join(o for _, o, _ in present).encode() + b"\n").stdout; pos = 0
            for p, o, k in present:
                nl = blob.index(b"\n", pos); size = int(blob[pos:nl].split()[2]); t = blob[nl+1:nl+1+size].decode(errors="replace"); pos = nl + 1 + size + 1
                if k == "gradle":
                    for l in t.splitlines():
                        if not comment(l): ht += [int(m.group(2)) for m in HT.finditer(l)]
                    continue
                for i, l in enumerate(t.splitlines(), 1):
                    if comment(l): continue
                    for key, (rx, kk) in RX.items():
                        if kk == k and rx.search(l): hits[key].append(f"{p}:{i}:{l.strip()[:160]}")
        res["hits"] = hits; res["head_target"] = max(ht) if ht else None
    except Exception as e:
        res["error"] = "scan:" + type(e).__name__ + ":" + str(e)[:150]
    return res
done = {json.loads(l)["pkg"] for l in open(out)} if os.path.exists(out) else set()
todo = [r for r in rows if r["pkg"] not in done]
with open(out, "a") as f, ThreadPoolExecutor(workers) as ex:
    for res in ex.map(one, todo): f.write(json.dumps(res) + "\n"); f.flush()
print("done", len(todo))
