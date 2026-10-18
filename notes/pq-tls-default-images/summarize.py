"""Summarize one run directory from the raw s_client output alone (no results.jsonl).

Usage: python3 summarize.py results/run2   (or out/ after your own run)
Per unit: PQ when all three default-client handshakes (M1) report `Negotiated TLS1.3 group: X25519MLKEM768`;
otherwise NO_PQ. M2 is the PQ-only client; a failed handshake shows `<NULL>` as its group.
Units with no handshake files (a target that did not start) print NO_HANDSHAKE.
"""
import re, sys
from pathlib import Path
raw = Path(sys.argv[1])
out = {}
for unit in sorted(p.name for p in raw.iterdir() if p.is_dir()):
    row = {}
    for m in ("M1", "M2"):
        vals = []
        for f in sorted((raw / unit).glob(f"{m}_*.txt")):
            t = f.read_text(errors="replace")
            g = re.search(r"^Negotiated TLS1\.3 group: (.+)$", t, re.M)
            k = re.search(r"^(?:Peer|Server) Temp Key: ([^,\n]+)", t, re.M)
            vals.append((g.group(1).strip() if g else None, k.group(1).strip() if k else None))
        row[m] = vals
    m1 = {v[0] for v in row["M1"]}
    if not row["M1"]:
        row["result"] = "NO_HANDSHAKE"
    else:
        row["result"] = "PQ" if m1 == {"X25519MLKEM768"} and len(row["M1"]) == 3 else "NO_PQ"
    out[unit] = row
for u, r in out.items():
    print(u, r["result"], "M1:", sorted(set(map(str, r["M1"]))), "M2:", sorted(set(map(str, r["M2"]))))
units = [u for u in out if re.fullmatch(r"U\d\d", u)]
print("images PQ:", sum(out[u]["result"] == "PQ" for u in units), "of", len(units))
