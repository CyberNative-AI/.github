"""POST HOC (after the frozen ruling): classify why R2 splits VTEC events.
Per split event, each R2 component is rooted at its earliest alert. A component whose earliest alert carries VTEC NEW is a
'parallel NEW root' (segments issued as separate CAP alerts); a component whose earliest alert carries another action
and has no resolvable reference to the same event is a 'chain restart'. Reports root action x messageType."""
import collections, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import analyze as A

alerts, _ = A.load(Path(sys.argv[1]))
comp = A.components(alerts, strict=True)
by_id = {a["id"]: a for a in alerts}
key_of, act_of, ev = {}, {}, collections.defaultdict(list)
for a in alerts:
    for s in (a.get("parameters") or {}).get("VTEC") or []:
        v = A.parse_vtec(s)
        if v and v["k"] == "O":
            key_of[a["id"]], act_of[a["id"]] = v["key"], v["action"]; ev[v["key"]].append(a["id"])
snap = {a["id"] for a in alerts if not a.get("_extra")}
evald = [k for k, ids in ev.items() if len(ids) >= 2 and any(act_of[i] == "NEW" and i in snap for i in ids)]
kinds, root_tab, restart_refs, ex = collections.Counter(), collections.Counter(), collections.Counter(), []
for k in evald:
    comps = collections.defaultdict(list)
    for i in ev[k]: comps[comp[i]].append(i)
    if len(comps) < 2: continue
    roots = [min(m, key=lambda i: A.parse_time(by_id[i]["sent"])) for m in comps.values()]
    restarts = [r for r in roots if act_of[r] != "NEW"]
    kinds["has_chain_restart" if restarts else "parallel_NEW_roots_only"] += 1
    for r in sorted(roots, key=lambda i: A.parse_time(by_id[i]["sent"]))[1:]:
        root_tab[(act_of[r], by_id[r]["messageType"])] += 1
    for r in restarts:
        refs = A.ref_ids(by_id[r])
        restart_refs["no_references" if not refs else ("refs_other_event_or_type" if all(key_of.get(x) != k for x in refs) else "refs_same_event?")] += 1
    if restarts and len(ex) < 6:
        r = restarts[0]; ex.append({"event": k, "root": r, "action": act_of[r], "messageType": by_id[r]["messageType"],
                                    "sent": by_id[r]["sent"], "awips": by_id[r]["parameters"].get("AWIPSidentifier"),
                                    "refs": A.ref_ids(by_id[r])[:3], "areaDesc": by_id[r]["areaDesc"][:80]})
out = {"split_events": sum(kinds.values()), "kinds": dict(kinds),
       "later_component_root_action_x_messageType": {f"{a}|{m}": n for (a, m), n in root_tab.most_common()},
       "restart_root_references": dict(restart_refs), "examples": ex}
Path(sys.argv[2]).write_text(json.dumps(out, indent=1) + "\n"); print(json.dumps(out, indent=1))
