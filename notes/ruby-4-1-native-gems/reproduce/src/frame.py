"""Frame: top-N rubygems by all-time downloads (ecosyste.ms), latest stable version, platforms,
and native-extension detection from rubygems.org quick gemspec (Marshal.4.8 .rz)."""
import json, sys, time, zlib, re, urllib.request, urllib.parse, concurrent.futures as cf, pathlib
UA = "cybernative-research/1.0 (+hello@cybernative.ai)"
OUT = pathlib.Path("data")
def get(url, raw=False, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                b = r.read(); return b if raw else json.loads(b)
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(3 * (i + 1))
        except Exception:
            time.sleep(3 * (i + 1))
    return "ERR"
def top(n):
    rows = []
    for p in range(1, n // 100 + 1):
        d = get(f"https://packages.ecosyste.ms/api/v1/registries/rubygems.org/packages?sort=downloads&order=desc&per_page=100&page={p}")
        rows += [{"rank": len(rows) + i + 1, "name": x["name"], "downloads": x["downloads"],
                  "downloads_period": x.get("downloads_period"), "repo": x.get("repository_url")} for i, x in enumerate(d)]
    return rows
EXT = re.compile(rb"([\w./-]*(?:extconf\.rb|mkrf_conf\.rb|CMakeLists\.txt|Cargo\.toml|configure))")
def meta(row):
    v = get(f"https://rubygems.org/api/v1/versions/{urllib.parse.quote(row['name'])}.json")
    if v in (None, "ERR"): return {**row, "error": "versions"}
    stable = [x for x in v if not x.get("prerelease")]
    if not stable: return {**row, "error": "no_stable"}
    latest = stable[0]["number"]
    plats = [{"platform": x["platform"], "ruby_version": x.get("ruby_version"), "created_at": x["created_at"]}
             for x in stable if x["number"] == latest]
    ruby_plat = any(p["platform"] == "ruby" for p in plats)
    exts = []
    if ruby_plat:
        rz = get(f"https://rubygems.org/quick/Marshal.4.8/{row['name']}-{latest}.gemspec.rz", raw=True)
        if rz in (None, "ERR"): return {**row, "latest": latest, "platforms": plats, "error": "spec"}
        spec = zlib.decompress(rz)
        exts = sorted({m.decode("utf-8", "replace") for m in EXT.findall(spec) if b"/" in m or m.endswith(b"extconf.rb")})
    return {**row, "latest": latest, "latest_date": plats[0]["created_at"], "platforms": plats,
            "ruby_platform": ruby_plat, "ext_hits": exts}
if __name__ == "__main__":
    n = int(sys.argv[1])
    rows = top(n); (OUT / "top.json").write_text(json.dumps(rows))
    with cf.ThreadPoolExecutor(6) as ex: res = list(ex.map(meta, rows))
    with open(OUT / "frame.jsonl", "w") as f:
        for r in res: f.write(json.dumps(r) + "\n")
    nat = [r for r in res if r.get("ext_hits") or any(p["platform"] != "ruby" for p in r.get("platforms", []))]
    print(len(res), "gems;", sum(1 for r in res if r.get("error")), "errors;", len(nat), "native candidates")
