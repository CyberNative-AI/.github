"""Positive control: synthetic alerts with known split / merge / exact events and end cases."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import analyze as A

def al(i, ev, vt, mt, sent, ends, refs=(), sender="NWS X"):
    return {"id": i, "event": ev, "senderName": sender, "messageType": mt, "sent": sent, "ends": ends, "expires": ends,
            "references": [{"identifier": r} for r in refs], "parameters": {"VTEC": [vt]} if vt else {}, "status": "Actual",
            "headline": "", "description": ""}

def V(act, etn, ph="SV", sig="W"): return f"/O.{act}.KXXX.{ph}.{sig}.{etn:04d}.261010T1200Z-261010T1300Z/"

T0, T1, T2 = "2026-10-10T12:00:00+00:00", "2026-10-10T12:30:00+00:00", "2026-10-10T13:00:00+00:00"
alerts = [
    # event 1: exact (NEW, CON, EXP; EXP sent at ends)
    al("a1", "Severe Thunderstorm Warning", V("NEW", 1), "Alert", T0, T2),
    al("a2", "Severe Thunderstorm Warning", V("CON", 1), "Update", T1, T2, ["a1"]),
    al("a3", "Severe Thunderstorm Warning", V("EXP", 1), "Update", T2, T2, ["a2"]),
    # event 2: split (CON lacks references)
    al("b1", "Severe Thunderstorm Warning", V("NEW", 2), "Alert", T0, T2),
    al("b2", "Severe Thunderstorm Warning", V("CAN", 2), "Cancel", T1, T2),
    # event 3 and 4: merged (event 4 update references event 3 alert, same event name)
    al("c1", "Severe Thunderstorm Warning", V("NEW", 3), "Alert", T0, T2),
    al("d1", "Severe Thunderstorm Warning", V("NEW", 4), "Alert", T0, T2),
    al("d2", "Severe Thunderstorm Warning", V("CON", 4), "Update", T1, T2, ["d1", "c1"]),
    # event 5 (watch) upgraded into event 6 (warning): R1 merges, R2 separates
    al("e1", "Winter Storm Watch", V("NEW", 5, "WS", "A"), "Alert", T0, T2),
    al("f1", "Winter Storm Warning", V("NEW", 6, "WS", "W"), "Alert", T1, T2, ["e1"]),
    al("e2", "Winter Storm Watch", V("UPG", 5, "WS", "A"), "Cancel", T1, T2, ["e1"]),
    # event 7: linked only through parameters.expiredReferences; its end is announced in text only
    al("g1", "Flood Advisory", V("NEW", 7, "FA", "Y"), "Alert", T0, "2026-10-10T15:00:00+00:00"),
    al("g2", "Flood Advisory", V("EXP", 7, "FA", "Y"), "Update", T1, "2026-10-10T15:00:00+00:00"),
]
alerts[-1]["parameters"]["expiredReferences"] = ["w-nws.webmaster@noaa.gov,g1,2026-10-10T12:00:00+00:00"]
alerts[-1]["headline"] = "The Flood Advisory will expire at 3:00 PM"
r = A.analyze(alerts, {"actual": len(alerts)})
r2, r1 = r["R2_references_same_event_sender"]["outcomes"], r["R1_references"]["outcomes"]
# primary evaluation = events with >= 2 alerts: 1 exact, 2 split, 4 merged (with 3), 5 exact (UPG kept apart), 7 exact
assert r2 == {"exact": 3, "split": 1, "merged": 1}, r2
assert r1 == {"exact": 2, "split": 1, "merged": 2}, r1
assert r["R2a_references_only_same_event_sender"]["outcomes"] == {"exact": 2, "split": 2, "merged": 1}
assert r["R0_no_edges"]["outcomes"] == {"split": 5}
assert r["R2_references_same_event_sender"]["eval_set_sensitivity"]["all_new_events"] == {"n": 7, "exact": 4, "share": 4 / 7}
p = r["P2_end_detection"]
assert p["E2_tol10"]["end_alerts"] == 4 and p["E2_tol10"]["end_detected"] == 4, p["E2_tol10"]
assert p["E1_tol0"]["end_detected"] == 2 and p["EX_tol0"]["end_detected"] == 1
assert p["E2_tol10"]["false_end"] == 0, p
assert A.decide({**r, "load": {"actual": 11}}).startswith("INVALID")
assert A.parse_vtec("/O.NEW.KICT.SV.W.0442.000000T0000Z-261014T0015Z/")["key"] == "KICT.SV.W.442"
assert A.parse_vtec("garbage") is None
print("ok", r2, r1)
