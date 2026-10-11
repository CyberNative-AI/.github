"""Check a resolved dependency set against Python 3.15 using PyPI metadata only (no installs, no builds).

usage: python cap315.py RESOLVED
  RESOLVED  pip --report JSON, or name==version lines (uv pip compile, pip freeze),
            resolved on the Python you use today

CAP:      this release's requires_python excludes 3.15. pip skips it; "newest uncapped" is the newest
          release whose requires_python admits 3.15 (pip may pick an older one, fail, or not finish).
          uv ignores the upper bound and installs this release anyway.
NO-WHEEL: this release ships version-specific wheels, none for 3.15 on any platform (no cp315,
          abi3 or py3; free-threaded cp315t wheels don't count). On 3.15 it builds from source,
          or cannot install if there is no source release.
SKIPPED:  not found on PyPI (private index, or a local version such as +cpu that PyPI lacks).
Exit status: 1 if any CAP, else 0."""
import json, re, sys, urllib.error, urllib.request
try:
    from packaging.specifiers import SpecifierSet, InvalidSpecifier
    from packaging.version import Version, InvalidVersion
except ImportError:
    from pip._vendor.packaging.specifiers import SpecifierSet, InvalidSpecifier
    from pip._vendor.packaging.version import Version, InvalidVersion

PY = "3.15.0"

def load(path):
    text = open(path).read()
    if text.lstrip().startswith("{"):
        pins = [(i["metadata"]["name"], i["metadata"]["version"]) for i in json.loads(text)["install"]]
    else:
        pins = re.findall(r"^([A-Za-z0-9._-]+)==([^\s;#]+)", text, re.M)
    return {re.sub(r"[-_.]+", "-", name).lower(): version for name, version in pins}

def pypi(*parts):
    url = "https://pypi.org/pypi/" + "/".join(parts) + "/json"
    return json.load(urllib.request.urlopen(url, timeout=60))

def admits(rp):
    try:
        return not rp or SpecifierSet(rp).contains(PY, prereleases=True)
    except InvalidSpecifier:
        return True

def has_315_wheel(files):
    tags = [f["filename"][:-4].split("-")[-3:] for f in files if f["filename"].endswith(".whl")]
    if not tags:
        return True  # sdist only: built on every Python version, nothing new on 3.15
    return any(("cp315" in py and not abi.endswith("t")) or abi == "abi3" or (abi == "none" and "py3" in py)
               for py, abi, _ in tags)

def installs_on_315(files):
    return has_315_wheel(files) or any(f["packagetype"] == "sdist" for f in files)

def fallback(name):
    best = None
    for v, files in pypi(name)["releases"].items():
        live = [f for f in files if not f.get("yanked")]
        try:
            V = Version(v)
        except InvalidVersion:
            continue
        if live and not V.is_prerelease and admits(live[0].get("requires_python")) and (best is None or V > best[0]):
            best = (V, min(f["upload_time_iso_8601"] for f in live)[:10], live)
    if not best:
        return "none"
    return "%s (%s)%s" % (best[0], best[1], "" if installs_on_315(best[2]) else ", no 3.15 file")

now = load(sys.argv[1])
capped = 0
for name, version in sorted(now.items()):
    try:
        d = pypi(name, version.split("+")[0])
    except urllib.error.HTTPError:
        print("SKIPPED   %-32s %-12s not found on PyPI" % (name, version))
        continue
    rp = d["info"].get("requires_python") or ""
    if not admits(rp):
        capped += 1
        print("CAP       %-32s %-12s requires_python %-16s newest uncapped: %s" % (name, version, rp, fallback(name)))
    elif not has_315_wheel(d["urls"]):
        how = "builds from source" if any(f["packagetype"] == "sdist" for f in d["urls"]) else "no source release"
        print("NO-WHEEL  %-32s %-12s no 3.15 wheel; %s" % (name, version, how))
print("%d packages checked, %d capped below 3.15" % (len(now), capped))
sys.exit(1 if capped else 0)
