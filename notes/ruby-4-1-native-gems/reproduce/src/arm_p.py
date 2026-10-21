"""Arm P: for frame gems whose latest version ships x86_64-linux / x86_64-linux-gnu builds, does the
build's required_ruby_version admit 4.1.0? (metadata from the rubygems.org versions API, data/frame.jsonl)"""
import json, re
def ok(req, v=(4, 1, 0)):
    if not req: return True
    for part in req.split(","):
        m = re.match(r"\s*(>=|<=|>|<|=|~>|!=)?\s*([\d.]+(?:\.[a-z]+\w*)?)", part.strip())
        op, ver = (m.group(1) or "="), m.group(2)
        nums = tuple(int(x) for x in re.findall(r"\d+", ver.split(".dev")[0].split("a")[0])[:3])
        pre = bool(re.search(r"[a-z]", ver))
        nv = nums + (0,) * (3 - len(nums))
        if op == "<" and not (v < nv): return False
        if op == "<=" and not (v <= nv): return False
        if op == ">=" and not (v >= nv): return False
        if op == ">" and not (v > nv): return False
        if op == "~>":
            hi = list(nums[:-1]); hi[-1] += 1
            if not (v >= nv and v < tuple(hi) + (0,) * (3 - len(hi))): return False
    return True
rows = [json.loads(l) for l in open("data/frame.jsonl")]
out = []
for r in rows:
    for p in r.get("platforms", []):
        if p["platform"] in ("x86_64-linux", "x86_64-linux-gnu"):
            out.append({"name": r["name"], "rank": r["rank"], "latest": r["latest"], "platform": p["platform"],
                        "ruby_version": p["ruby_version"], "admits_4_1": ok(p["ruby_version"]),
                        "has_source_build": r.get("ruby_platform")})
json.dump(out, open("data/arm_p.json", "w"), indent=1)
n = len(out); bad = [o for o in out if not o["admits_4_1"]]
print(n, "linux precompiled builds;", len(bad), "do not admit 4.1.0")
for o in out: print(o["rank"], o["name"], o["latest"], o["platform"], o["ruby_version"], o["admits_4_1"])
