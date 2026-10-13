"""AMENDMENT-03 (post-result): label each confirmed consequential divergent call shape using the real-input arm
(results/real-*.jsonl) and root checks; recompute R on hosted runners. Labels are per command, written before counting."""
import collections, json, math
LABEL = {
    "base64": ("no_working_step_breaks", "real secrets (single-line, wrapped-76, extra newlines) identical; differences only on invalid input: uutils more lenient (CRLF, unpadded->GNU 9.7 too) or writes no partial bytes where GNU 9.4 also exits 1"),
    "cut": ("fixture_only", "all sampled contexts cut ASCII git SHAs (identical); differs only on non-ASCII (uutils counts characters, GNU bytes)"),
    "nproc": ("environment_only", "differs only under a cgroup CPU quota (docker --cpus): uutils reports the quota, GNU 9.4/9.7 the affinity count; identical without quota and with cpuset"),
    "date": ("placeholder_artifact", "divergence came from the 'd1' expansion placeholder; 20 realistic -d strings x 3 formats identical (60/60)"),
    "install": ("nonroot_artifact", "as root (sudo, as in the workflows) identical rc/mode/owner"),
}
def wilson(k, n, z=1.96):
    ph = k / n; d = 1 + z * z / n; c = (ph + z * z / (2 * n)) / d
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return [round(max(0, c - h), 5), round(c + h, 5)]
d = [json.loads(l) for l in open("results/divergent.jsonl")]
out = {"labels": LABEL}
for st, n in (("random-dedup", 1297), ("top", 175)):
    rows = [r for r in d if r["stratum"] == st]
    by = collections.defaultdict(set)
    for r in rows: by[r["argv"][0]].add(r["repo"])
    breaking = {r["repo"] for r in rows if LABEL[r["argv"][0]][0] not in ("no_working_step_breaks", "fixture_only", "environment_only", "placeholder_artifact", "nonroot_artifact")}
    out[st] = {"mechanical_repos": len({r["repo"] for r in rows}), "repos_by_command": {k: len(v) for k, v in sorted(by.items())},
               "hosted_runner_breaking_repos": len(breaking), "R_adjudicated": round(len(breaking) / n, 5), "wilson95": wilson(len(breaking), n),
               "nproc_quota_exposed_repos": len(by.get("nproc", ())), "base64_decode_repos": len(by.get("base64", ()))}
json.dump(out, open("results/ADJUDICATION.json", "w"), indent=1, sort_keys=True)
print(json.dumps({k: v for k, v in out.items() if k != "labels"}, indent=1))
