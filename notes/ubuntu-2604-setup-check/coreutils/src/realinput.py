"""Post-hoc real-input arm (AMENDMENT-03): realistic inputs for the divergent call shapes. Same container/arms/env as harness.
usage: realinput.py ARM OUT"""
import base64, hashlib, json, os, random, subprocess, sys
ARM = sys.argv[1]
PATH = {"gnu94": "/usr/bin:/bin", "uutils": "/usr/bin:/bin", "gnu97": "/opt/gnu97:/usr/bin:/bin"}[ARM]
ENV = {"PATH": PATH, "LANG": "C.UTF-8", "HOME": "/work", "FAKETIME": "2026-10-12 12:00:00",
       "LD_PRELOAD": "/usr/lib/x86_64-linux-gnu/faketime/libfaketime.so.1", "NO_FAKE_STAT": "1", "DONT_FAKE_MONOTONIC": "1"}
rnd = random.Random(13253)
blob = bytes(rnd.randrange(256) for _ in range(2500))  # keystore-sized binary
std = base64.b64encode(blob).decode()
wrapped = "\n".join(std[i:i + 76] for i in range(0, len(std), 76))
unpadded_blob = blob[:2501 - 2]  # length not multiple of 3 -> padding present in std form
b2 = base64.b64encode(blob[:2498]).decode()
INPUTS = {
    "single_line+nl": std + "\n",                       # echo "$X" (secret pasted on one line)
    "single_line_noNL": std,                            # printf '%s' "$X"
    "wrapped76+nl": wrapped + "\n",                     # echo "$X", secret made with `base64 file`
    "wrapped_collapsed_spaces+nl": wrapped.replace("\n", " ") + "\n",  # echo $X unquoted
    "wrapped_crlf": wrapped.replace("\n", "\r\n") + "\r\n",           # pasted from Windows
    "trailing_space+nl": std + " \n",
    "unpadded+nl": b2.rstrip("=") + "\n",               # padding stripped (JWT/url tools)
    "urlsafe+nl": base64.urlsafe_b64encode(blob).decode() + "\n",
    "double_nl_end": std + "\n\n",
    "pem_like_text": base64.b64encode(b"-----BEGIN PRIVATE KEY-----\nMIIabc\n-----END PRIVATE KEY-----\n").decode() + "\n",
}
CMDS = [["base64", "-d"], ["base64", "--decode"], ["base64", "-id"], ["base64", "-d", "-i"]]
DATES = ["+5 hours", "3 days ago", "-1 days", "1 day ago", "yesterday", "tomorrow", "next monday", "last friday",
         "@1700000000", "2026-10-01", "2026-10-01T12:34:56Z", "2026-10-01 12:34:56 +0200", "now", "today",
         "+1 week", "-30 minutes", "1 month ago", "first day of next month", "Oct 1 2026", "2 weeks ago 00:00"]
DFMT = ["+%Y-%m-%dT%H:%M:%SZ", "+%s", "+%Y-%m-%d"]
CUTS = [("ascii_sha", "3f786850e387550fdab836ed7e6dc881de23001b\n"), ("nonascii_subject", "fix: café menü — ünïcode ✓ done\n")]
rows = []
def run(argv, stdin=b""):
    p = subprocess.run(argv, input=stdin, env=ENV, capture_output=True, timeout=10, cwd="/work")
    return {"rc": p.returncode, "out_sha": hashlib.sha256(p.stdout).hexdigest()[:16], "out_len": len(p.stdout),
            "out_ok": p.stdout == blob, "err": p.stderr[:160].decode("utf-8", "replace"), "out": p.stdout[:60].decode("utf-8", "backslashreplace")}
for name, txt in INPUTS.items():
    for c in CMDS:
        rows.append({"k": ["base64", name, c], **run(c, txt.encode())})
for s in DATES:
    for f in DFMT:
        rows.append({"k": ["date", s, f], **run(["date", "-u", "-d", s, f])})
for nm, txt in CUTS:
    for c in (["cut", "-c1-7"], ["cut", "-c1-12"], ["cut", "-b1-7"]):
        rows.append({"k": ["cut", nm, c], **run(c, txt.encode())})
rows.append({"k": ["nproc"], **run(["nproc"])})
open(sys.argv[2], "w").write("".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows))
