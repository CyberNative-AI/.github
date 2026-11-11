"""Dated outcome read (h = 14 d), written 2026-11-11 after the rules were fixed; outcome only, no new ruling.

Usage: python3 -I src/h14_read.py RUNDIR BASEDIR
  RUNDIR  = fetch.py output with --read-time 2026-11-11T12:00:00Z
  BASEDIR = fetch.py output with --read-time 2026-10-28T12:03:06Z (defines F1 = the batch items seen at the 10-28 read;
            any later F item is F2)

fetch.py reads timelines only for items closed within 72 h (TIMELINE_H). For the 14 d horizon this script adds the
missing timeline reads for F items closed after 72 h and within 14 d (unmerged PRs and issues), saved as
raw/timeline-extra-*.json in the same MANIFEST, then applies compute.outcome() unchanged at h = 336.
Writes RUNDIR/out/h14.json.
"""
import collections
import datetime as dt
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import compute as co  # noqa: E402
import fetch as fe  # noqa: E402

H = 336


def main():
    run, base = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    meta = json.loads((run / "data" / "fetch-meta.json").read_text())
    read_time = co.t(meta["read_time"])
    rows = [json.loads(l) for l in open(run / "data" / "items.jsonl", encoding="utf-8")]
    f1_numbers = {json.loads(l)["number"] for l in open(base / "data" / "items.jsonl", encoding="utf-8")
                  if json.loads(l)["group"] == "F"}
    F = [r for r in rows if r["group"] == "F"]

    api = None
    extra = []
    for r in F:
        if "closers" in r or not r["closed_at"]:
            continue
        age = (co.t(r["closed_at"]) - co.t(r["created_at"])).total_seconds() / 3600
        if age > H or (r["is_pr"] and r.get("merged_at")):
            continue
        if api is None:
            api = fe.Api(run, fe.load_token())
        ev, page = [], 1
        while True:
            tl = api.get(f"/repos/{fe.REPO}/issues/{r['number']}/timeline?per_page=100&page={page}",
                         f"timeline-extra-{r['number']}-p{page}")
            ev += tl
            if len(tl) < 100:
                break
            page += 1
        r["closed_commit_ids"] = [x.get("commit_id") for x in ev if x.get("event") == "closed" and x.get("commit_id")]
        r["closers"] = [(x.get("actor") or {}).get("login") for x in ev if x.get("event") == "closed"]
        r["xref_prs"] = [{"number": s["number"], "merged_at": s["pull_request"].get("merged_at"),
                          "login": (s.get("user") or {}).get("login")}
                         for x in ev if x.get("event") == "cross-referenced"
                         for s in [((x.get("source") or {}).get("issue") or {})]
                         if s.get("pull_request") and (s.get("repository") or {}).get("full_name") == fe.REPO]
        extra.append(r["number"])

    def summarize(rs):
        out = {}
        for kind, sel in (("pr", [r for r in rs if r["is_pr"]]), ("pr_small", [r for r in rs if r["is_pr"] and co.small(r)]),
                          ("issue", [r for r in rs if not r["is_pr"]])):
            oc = collections.Counter(co.outcome(r, H, read_time) for r in sel)
            ineligible = oc.pop(None, 0)
            rc = collections.Counter(co.raw_outcome(r, H, read_time) for r in sel)
            rc.pop(None, None)
            n = sum(oc.values())
            k = oc.get("ACCEPTED", 0)
            state = collections.Counter("merged" if r.get("merged_at") else f"{r['state']}:{r.get('state_reason')}" for r in sel)
            out[kind] = {"n_total": len(sel), "n_eligible_h14": n, "ineligible_h14": ineligible,
                         "outcomes_h14": dict(sorted(oc.items())), "accepted_h14_wilson": co.wilson(k, n),
                         "raw_h14": dict(sorted(rc.items())), "state_at_read": dict(sorted(state.items()))}
        mergers = collections.Counter(r.get("merged_by") for r in rs if r["is_pr"] and r.get("merged_at"))
        out["mergers_at_read"] = dict(mergers.most_common())
        fixers = collections.Counter()
        for r in rs:
            if not r["is_pr"] and co.outcome(r, H, read_time) == "ACCEPTED":
                for x in r.get("xref_prs", []):
                    if x["merged_at"]:
                        fixers[x["login"]] += 1
        out["issue_fix_pr_authors_h14"] = dict(fixers.most_common())
        return out

    F1 = [r for r in F if r["number"] in f1_numbers]
    F2 = [r for r in F if r["number"] not in f1_numbers]
    lost = sorted(f1_numbers - {r["number"] for r in F})
    O = [r for r in rows if r["group"] == "O_prior" and r["is_pr"]]
    o_raw = {}
    for name, sel in (("O_prior_pr", O), ("O_small_prior_pr", [r for r in O if co.small(r)])):
        rc = collections.Counter(co.raw_outcome(r, H, read_time) for r in sel)
        rc.pop(None, None)
        o_raw[name] = {"raw_h14": dict(sorted(rc.items())), "merged_rate_wilson": co.wilson(rc.get("MERGED", 0), sum(rc.values()))}
    res = {"read_time": meta["read_time"], "horizon_h": H, "extra_timelines": sorted(extra),
           "extra_calls": api.calls if api else 0, "F1": summarize(F1), "F2": summarize(F2),
           "F2_items": [{k: r.get(k) for k in ("number", "is_pr", "login", "created_at", "state", "title")} for r in F2],
           "F1_missing_from_run3": lost,
           "O_prior_raw_h14_context_only": o_raw}
    (run / "out").mkdir(exist_ok=True)
    (run / "out" / "h14.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: res[k] for k in ("extra_calls", "F1_missing_from_run3")} |
                     {"F1": {k: res["F1"][k] for k in ("pr", "pr_small", "issue")}, "n_F2": len(F2)}, indent=1))


if __name__ == "__main__":
    main()
