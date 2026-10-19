"""Check the note's census totals and recorded test results from the files in this directory, and that each
recipe class has a pinned source. With --fetch, also download every pinned recipe, verify its SHA-256 and
derive the recipe class again from its bytes. Python 3, standard library only.
Prints PASS/FAIL per statement; exits 1 on any FAIL."""
import csv, hashlib, re, sys, urllib.request
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
fails = 0


def check(label, ok):
    global fails
    print(("PASS " if ok else "FAIL ") + label)
    fails += 0 if ok else 1


def ver(s):
    return tuple(int(x) for x in s.split("."))


def runtime_class(path):
    """Last `curl -V` in the file (after the package install) decides: OLD < 8.20.0, else NTLM present or not."""
    t = path.read_text(errors="replace")
    found = re.findall(r"^curl (\d+\.\d+\.\d+)[^\n]*\n(?:[^\n]*\n)*?Features:([^\n]*)", t, re.M)
    if not found:
        return None, None, None
    v, feats = found[-1]
    feats = feats.split()
    cls = "OLD" if ver(v) < (8, 20, 0) else ("KEPT" if "NTLM" in feats else "DROPPED")
    return cls, v, feats


rows = list(csv.DictReader((HERE / "census.csv").open()))
frame = [r for r in rows if r["in_frame"] == "yes"]
tally = Counter(r["class"] for r in frame)
check(f"frame has 22 channels (got {len(frame)})", len(frame) == 22)
check(f"17 DROPPED / 3 KEPT / 2 OLD (got {dict(tally)})", tally == Counter(DROPPED=17, KEPT=3, OLD=2))
check("DROPPED rows are all curl >= 8.20.0", all(ver(r["curl_version"]) >= (8, 20, 0) for r in frame if r["class"] == "DROPPED"))
check(f"{sum(1 for r in frame if r['runtime_file'])} channels read by installing curl in the image, "
      f"{sum(1 for r in frame if not r['runtime_file'])} by packaging recipe only",
      sum(1 for r in frame if r["runtime_file"]) == 11)

for r in rows:
    if not r["runtime_file"]:
        continue
    cls, v, feats = runtime_class(HERE / r["runtime_file"])
    check(f"{r['channel']}: curl -V says {v}, {cls}; census says {r['curl_version']}, {r['runtime_class']}",
          cls == r["runtime_class"] and v == r["curl_version"])

u = (HERE / "runtime/ubuntu-rolling.txt").read_text()
check("ubuntu:rolling is Ubuntu 26.10", 'PRETTY_NAME="Ubuntu 26.10"' in u)
check("Ubuntu 26.04 (ubuntu:latest) still has NTLM, curl 8.18.0",
      runtime_class(HERE / "runtime/ubuntu-latest-extra.txt")[:2] == ("OLD", "8.18.0")
      and "NTLM" in runtime_class(HERE / "runtime/ubuntu-latest-extra.txt")[2])
nospnego = sorted(p.stem for p in (HERE / "runtime").glob("*.txt")
                  if runtime_class(p)[0] == "DROPPED" and "SPNEGO" not in runtime_class(p)[2])
check(f"images without NTLM that also lack SPNEGO: {nospnego}", nospnego == ["alpine-edge", "alpine-latest"])

m = (HERE / "proxy-test.txt").read_text()
def tag(text, name):
    hit = re.search(rf"^TAG {re.escape(name)} (.*)$", text, re.M)
    return hit.group(1) if hit else ""
check("control: 8.23.0 default build lacks NTLM", "NTLM" not in tag(m, "C-default").split("Features:")[1].split())
check("control: 8.23.0 --enable-ntlm build has NTLM", "NTLM" in tag(m, "C-ntlm").split("Features:")[1].split())
check("control: Debian 13 curl 8.14.1 has NTLM", "NTLM" in tag(m, "C+").split("Features:")[1].split())
check("NTLM curl --proxy-ntlm: 200", tag(m, "M-a-trixie-proxy-ntlm").startswith("rc=0 http=200")
      and tag(m, "M-a2-ntlm-build-proxy-ntlm").startswith("rc=0 http=200"))
b = tag(m, "M-b-default-proxy-ntlm")
check("default 8.23.0 --proxy-ntlm: exit 2, 'does not support this'",
      b.startswith("rc=2") and "option --proxy-ntlm: the installed libcurl version does not support this" in b)
for name in ["M-c-default-proxy-anyauth", "M-c2-default-env-proxy", "M-c0-default-no-auth"]:
    check(f"{name}: exit 0, HTTP 407", tag(m, name).startswith("rc=0 http=407"))
check("NTLM curl --proxy-anyauth: 200", tag(m, "M-e-trixie-anyauth").startswith("rc=0 http=200"))
check("cntlm NTLMv2 bridge to the fake proxy: 407, 'Cannot do NTLMv2'",
      tag(m, "M-d-default-via-cntlm").startswith("rc=0 http=407") and "Cannot do NTLMv2!" in m)
c = (HERE / "cntlm-ntlmv1.txt").read_text()
check("cntlm NTLMv1 bridge to the fake proxy: 200", tag(c, "M-p1-plain-via-cntlm-ntlmv1").startswith("rc=0 http=200"))

pa = (HERE / "php-alpine.txt").read_text()
pl = (HERE / "php-latest.txt").read_text()
check("php:alpine is Alpine 3.24, PHP 8.5.11, libcurl 8.22.0, NTLM bit 0",
      'Alpine Linux v3.24' in pa and "TAG php 8.5.11 libcurl 8.22.0 NTLM_bit=0" in pa)
check("php:alpine CURLAUTH_NTLM: setopt false, errno 0, HTTP 407", tag(pa, "php-NTLM").startswith("setopt=false errno=0 http=407"))
check("php:alpine CURLAUTH_ANY: setopt true, errno 0, HTTP 407", tag(pa, "php-ANY").startswith("setopt=true errno=0 http=407"))
check("php:latest is Debian 13, libcurl 8.14.1, NTLM bit 1", "trixie" in pl and "libcurl 8.14.1 NTLM_bit=1" in pl)
check("php:latest CURLAUTH_NTLM: 200", tag(pl, "php-NTLM").startswith("setopt=true errno=0 http=200"))

f = (HERE / "fail-test.txt").read_text()
check("alpine:3.24 own curl 8.22.0 lacks NTLM", "TAG curl curl 8.22.0" in f and "NTLM" not in tag(f, "curl").split("Features:")[1].split())
check("alpine:3.24 --proxy-anyauth: exit 0, HTTP 407", tag(f, "anyauth").startswith("rc=0 http=407"))
check("alpine:3.24 --proxy-anyauth --fail: exit 22, HTTP 407", tag(f, "anyauth-fail").startswith("rc=22 http=407"))

# Recipes: we classified them by hand. Offline, check that every recipe class has pinned sources and that
# recipe and installed curl agree wherever both were read; --fetch derives each recipe class again.
src = list(csv.DictReader((HERE / "recipe-sources.csv").open()))
pinned = {s["pinned_url"]: s for s in src if s["status"] in ("PINNED", "POSTHOC head at capture time")}
recipe_rows = [r for r in frame if r["recipe_class"]]
check(f"{len(recipe_rows)} channels have a recipe class, each with a pinned recipe link and its full SHA-256",
      len(recipe_rows) == 19 and all(r["recipe_url"] in pinned and pinned[r["recipe_url"]]["sha256"] == r["recipe_sha256"]
                                     and pinned[r["recipe_url"]]["channel"] == r["channel"] for r in recipe_rows))
check("every pinned link is a fixed commit", all(s["pinned_commit"] and s["pinned_commit"] in s["pinned_url"] for s in pinned.values()))
both = [r for r in frame if r["recipe_class"] and r["runtime_class"]]
check(f"recipe and installed curl agree where both were read: {len(both)} channels",
      len(both) == 8 and all(r["recipe_class"] == r["runtime_class"] for r in both))
check("class is the installed result where installed, else the recipe result",
      all(r["class"] == (r["runtime_class"] or r["recipe_class"]) for r in frame))

VERSION = [r"^pkgver=(\d+\.\d+\.\d+)", r"^Version:\s*(\d+\.\d+\.\d+)", r'^\s*version:\s*"?(\d+\.\d+\.\d+)',
           r'version = "(\d+\.\d+\.\d+)"', r"^version\s*=?\s*(\d+\.\d+\.\d+)", r'"version":\s*"(\d+\.\d+\.\d+)"',
           r"curl-(\d+\.\d+\.\d+)\.tar", r"CURL_VER_='(\d+\.\d+\.\d+)'", r"^curl \((\d+\.\d+\.\d+)"]


def version_of(url, text):
    hit = re.search(r"/curl-(\d+\.\d+\.\d+)\.ebuild$", url)
    if hit:
        return hit.group(1)
    for pat in VERSION:
        hit = re.search(pat, text, re.M)
        if hit:
            return hit.group(1)
    return None


if "--fetch" in sys.argv[1:]:
    texts = {}
    for url, s in sorted(pinned.items()):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "curl-ntlm-note-check"}), timeout=30) as resp:
                body = resp.read()
        except Exception as e:  # noqa: BLE001 - report and count as a failure
            body = b""
            print(f"     {url}: {e}")
        check(f"{s['channel']} {s['role']}: pinned bytes match SHA-256 {s['sha256'][:16]}...", hashlib.sha256(body).hexdigest() == s["sha256"])
        texts[url] = body.decode("utf-8", errors="replace")
    for r in recipe_rows:
        mine = [s for s in pinned.values() if s["channel"] == r["channel"]]
        vfiles = [s for s in mine if "version" in s["role"]] or mine
        versions = {version_of(s["pinned_url"], texts[s["pinned_url"]]) for s in vfiles} - {None}
        recipe_text = "\n".join(texts[s["pinned_url"]] for s in mine if "recipe" in s["role"])
        v = versions.pop() if len(versions) == 1 else None
        on = re.search(r"--enable-ntlm\b|CURL_ENABLE_NTLM=ON", recipe_text, re.I) is not None
        cls = None if v is None else ("OLD" if ver(v) < (8, 20, 0) else ("KEPT" if on else "DROPPED"))
        check(f"{r['channel']}: pinned recipe says {v}, {cls}; census says {r['curl_version']}, {r['recipe_class']}",
              v == r["curl_version"] and cls == r["recipe_class"])

print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAIL'}")
sys.exit(1 if fails else 0)
