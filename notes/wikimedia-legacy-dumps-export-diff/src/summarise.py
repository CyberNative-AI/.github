"""Apply the frozen verdict rules (PROTOCOL.md section 6) to evidence/compare/** and write evidence/summary.json."""
from __future__ import annotations

import json

from common import EVID, W_END, read_json, write_json


def confirmed(c: dict, side: str) -> int:
    return c["live"].get(side, 0)


def main() -> int:
    s = read_json(EVID / "sample.json")
    sample = [x["wiki"] for x in s["sample"]]
    rows, unusable = {}, []
    for arm, wikis in (("current", sample + s["targeted"]), ("history", s["history_arm"])):
        for w in wikis:
            p = EVID / "compare" / arm / f"{w}.json"
            if not p.exists():
                unusable.append(f"{arm}:{w}:no-compare")
                continue
            c = read_json(p)
            if not c["rc_covers_window"]:
                unusable.append(f"{arm}:{w}:rc-window")
            if any(t and t >= W_END for t in c["max_ts"].values()):
                unusable.append(f"{arm}:{w}:snapshot-after-W")
            rows[f"{arm}:{w}"] = {
                "n_legacy": c["n_legacy"], "n_export": c["n_export"], "counts": c["counts"],
                "unexplained_primary": c["unexplained_primary"], "live_checked": c["live_checked"], "live": c["live"],
                "export_wrong": confirmed(c, "EXPORT_WRONG"), "legacy_wrong": confirmed(c, "LEGACY_WRONG"),
                "est_export_wrong": c["est_export_wrong"], "est_legacy_wrong": c["est_legacy_wrong"],
                "export_wrong_by_ns_type": c["export_wrong_by_ns_type"],
                "integrity": c["integrity"], "max_ts": c["max_ts"],
            }
    def usable(key: str) -> bool:
        return key in rows and not any(u.startswith(key + ":") for u in unusable)

    bad_sample = [w for w in sample if usable(f"current:{w}") and rows[f"current:{w}"]["export_wrong"] >= 1]
    n_unusable_hist = sum(1 for w in s["history_arm"] if not usable(f"history:{w}"))
    hist_valid = n_unusable_hist <= 4
    bad_hist = [w for w in s["history_arm"] if usable(f"history:{w}") and rows[f"history:{w}"]["export_wrong"] >= 1]
    big = [k for k, r in rows.items() if usable(k) and r["est_export_wrong"] >= 100
           and (hist_valid or not k.startswith("history:"))]
    legacy_side = [k for k, r in rows.items() if r["legacy_wrong"] >= 1]
    any_export = [k for k, r in rows.items() if usable(k) and r["export_wrong"] >= 1
                  and (hist_valid or not k.startswith("history:"))]
    n_unusable_sample = sum(1 for w in sample if not usable(f"current:{w}"))
    ctl = read_json(EVID / "control.json") if (EVID / "control.json").exists() else {"pass": False}
    if n_unusable_sample > 4 or not ctl["pass"]:
        verdict = "INVALID"
    elif len(bad_sample) >= 2 or big or (hist_valid and len(bad_hist) >= 2):
        verdict = "CONTINUE"
    elif any_export:
        verdict = "CHANGE"
    else:
        verdict = "STOP"
    out = {"verdict": verdict, "sample_wikis_with_confirmed_export_defect": bad_sample,
           "history_wikis_with_confirmed_export_defect": bad_hist, "arms_with_ge100_export_defects": big,
           "arms_with_confirmed_legacy_defect": legacy_side, "unusable": unusable,
           "history_arm_valid": hist_valid, "control_pass": ctl["pass"], "arms_with_any_export_defect": any_export,
           "coverage": s["coverage"]["missing_by_status"], "coverage_missing_n": len(s["coverage"]["missing_current_export"]),
           "rows": rows}
    write_json(EVID / "summary.json", out)
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
