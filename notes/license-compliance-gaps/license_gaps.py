#!/usr/bin/env python3
"""Which dependencies in a repository's GitHub dependency graph have no license?

Reads the SBOM that GitHub exports from the dependency graph (the same license
data GitHub's license compliance check and dependency review use) and counts the
entries whose licenseConcluded and licenseDeclared are both NOASSERTION.

    python3 license_gaps.py owner/repo [owner/repo ...]     # one line per repo
    python3 license_gaps.py owner/repo --list               # also list each entry
    python3 license_gaps.py --top Java Ruby JavaScript Python Go --n 9
    python3 license_gaps.py --sbom-dir raw/ --repos sample.txt   # rerun from saved files

One API request per repository (plus one per language for --top). Without a
token GitHub allows 60 requests an hour; set GITHUB_TOKEN for private repos.
Standard library only.
"""
import argparse, json, os, re, sys, urllib.parse, urllib.request

API = "https://api.github.com"
# An exact version: 1.2.3, v2, 4.0.0-rc.1, 1.0.0+build. Ranges (^1.2, ~>3, >=2),
# dist-tags (latest), 1.x, git/file specs and empty versions are "unresolved".
EXACT = re.compile(r"v?\d+(\.\d+)*([-.+][0-9A-Za-z.\-]+)?")
WILDCARD = re.compile(r"(^|\.)[xX*](\.|$)")


def get(path):
    req = urllib.request.Request(API + path, headers={
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "license-gaps"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"message": f"HTTP {e.code}"}


def kind(version):
    if not version:
        return "unresolved"
    if EXACT.fullmatch(version) and not WILDCARD.search(version):
        return "exact"
    return "unresolved"


def classify(sbom):
    """Return (rows, licensed_bases): one row per entry except the repo itself."""
    rows, licensed = [], set()
    for p in sbom.get("packages", []):
        purl = next((r["referenceLocator"] for r in p.get("externalRefs", [])
                     if r.get("referenceType") == "purl"), None)
        if not purl:
            continue
        eco = purl.split(":", 1)[1].split("/", 1)[0]
        if eco == "github":          # the repository itself
            continue
        no_license = all((p.get(k) or "NOASSERTION") == "NOASSERTION"
                         for k in ("licenseConcluded", "licenseDeclared"))
        # Split before unquoting: a scoped npm name is pkg:npm/%40scope/name.
        base = urllib.parse.unquote(purl.split("@", 1)[0])
        cat = "action" if eco == "githubactions" else kind(p.get("versionInfo") or "")
        rows.append((eco, cat, no_license, base, purl))
        if not no_license:
            licensed.add(base)
    return rows, licensed


def summarize(name, sbom, show_list):
    rows, licensed = classify(sbom)
    n = len(rows)
    nolic = [r for r in rows if r[2]]
    act = sum(1 for r in nolic if r[1] == "action")
    exact = sum(1 for r in nolic if r[1] == "exact")
    unres = sum(1 for r in nolic if r[1] == "unresolved")
    only = sum(1 for r in nolic if r[1] != "action" and r[3] not in licensed)
    print(f"{name}\t{n}\t{len(nolic)}\t{act}\t{unres}\t{exact}\t{only}")
    if show_list:
        for eco, cat, _, base, purl in sorted(nolic):
            note = "" if cat == "action" or base not in licensed else "\t(same package has a license elsewhere in this graph)"
            print(f"  {cat}\t{purl}{note}")
    return rows, licensed


def top_repos(langs, n):
    out = []
    for lang in langs:
        q = urllib.parse.quote(f"language:{lang} stars:>20000 archived:false")
        d = get(f"/search/repositories?q={q}&sort=stars&order=desc&per_page={n}")
        out += [i["full_name"] for i in d.get("items", [])[:n]]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("repos", nargs="*", help="owner/repo")
    ap.add_argument("--list", action="store_true", help="list every no-license entry")
    ap.add_argument("--top", nargs="+", metavar="LANG", help="most-starred repos per language")
    ap.add_argument("--n", type=int, default=9)
    ap.add_argument("--sbom-dir", help="read sbom-owner_repo.json files instead of the API")
    ap.add_argument("--repos-file", "--repos", dest="repos_file", help="file with one owner/repo per line")
    a = ap.parse_args()
    repos = list(a.repos)
    if a.repos_file:
        repos += open(a.repos_file).read().split()
    if a.top:
        repos += top_repos(a.top, a.n)
    if not repos:
        ap.error("give owner/repo, --repos-file or --top")
    print("repo\tentries\tno_license\tactions\tunresolved\texact\tno_license_anywhere_in_graph")
    tot = {"action": [0, 0], "exact": [0, 0], "unresolved": [0, 0]}
    also = only = with_deps = 0
    for name in repos:
        if a.sbom_dir:
            d = json.load(open(os.path.join(a.sbom_dir, "sbom-" + name.replace("/", "_") + ".json")))
        else:
            d = get(f"/repos/{name}/dependency-graph/sbom")
        if "sbom" not in d:
            print(f"{name}\tERROR {d.get('message')}")
            continue
        rows, licensed = summarize(name, d["sbom"], a.list)
        with_deps += bool(rows)
        for eco, cat, nl, base, _ in rows:
            tot[cat][0] += 1
            tot[cat][1] += nl
            if nl and cat != "action":
                if base in licensed:
                    also += 1
                else:
                    only += 1
    if len(repos) > 1:
        print(f"\n{with_deps} repositories with at least one dependency entry")
        for cat in ("action", "unresolved", "exact"):
            t, nl = tot[cat]
            pct = f"{100 * nl / t:.1f}%" if t else "-"
            print(f"{cat}: {nl} of {t} entries have no license ({pct})")
        print(f"non-action entries with no license: {also + only}; "
              f"same package licensed elsewhere in the graph: {also}; nowhere: {only}")


if __name__ == "__main__":
    main()
