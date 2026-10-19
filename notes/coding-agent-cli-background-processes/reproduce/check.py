"""Recompute the note's process and footprint statements from runs/*.json.

usage: python3 check.py   (standard library only; exits 1 on any mismatch)
"""
import json
import pathlib
import sys

RUNS = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (pathlib.Path(__file__).parent / "runs").glob("*.json")}
AFTER_B = ["10 s after window B closed", "60 s after window B closed", "180 s after window B closed", "330 s after window B closed"]
fails = []


def check(name, ok):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


def cmds(run, label):
    return [p["cmd"] for p in RUNS[run]["processes"].get(label, [])]


def mb(run, entry):
    return RUNS[run]["home_footprint"]["top_level_dirs"][entry]["bytes"] / 1e6


# Two leave a background process through 330 s after window B; seven leave nothing at any B check.
for run in ("codex", "opencode2", "ctl-daemon"):
    check(f"{run}: a process is alive at every check after window B", all(cmds(run, l) for l in AFTER_B))
for run in ("opencode1", "claude", "qwen", "crush", "kilo", "copilot", "codex-opt", "opencode2-opt", "ctl-plain"):
    check(f"{run}: nothing alive at any check", not any(cmds(run, l) for l in RUNS[run]["processes"]))
c330 = cmds("codex", "330 s after window B closed")
check("codex: managed daemon and pid-update-loop alive at 330 s, parent PID 1",
      any("--managed-daemon" in c for c in c330) and any("pid-update-loop" in c for c in c330)
      and all(p["ppid"] == 1 for p in RUNS["codex"]["processes"]["330 s after window B closed"]))
check("codex: both processes already present 10 s after window A",
      len(cmds("codex", "10 s after window A closed")) == 2)
check("opencode2: 'serve --service' alive at 330 s", any("serve --service" in c for c in cmds("opencode2", "330 s after window B closed")))
# Gemini: client still alive 10 s after each window, gone by 60 s.
check("gemini: alive at A+10 and B+10, nothing from B+60 on",
      bool(cmds("gemini", "10 s after window A closed")) and bool(cmds("gemini", "10 s after window B closed"))
      and not any(cmds("gemini", l) for l in AFTER_B[1:])
      and all("gemini" in c for l in ("10 s after window A closed", "10 s after window B closed") for c in cmds("gemini", l)))
# Stop commands.
s = RUNS["codex"]["stop_command"]
check("codex stop: exit 0 and status stopped", s["exit_code"] == 0 and '"status":"stopped"' in s["output"])
for l in ("10 s after the stop command", "60 s after the stop command", "330 s after the stop command"):
    left = cmds("codex", l)
    check(f"codex stop: only pid-update-loop left ({l})", len(left) == 1 and "pid-update-loop" in left[0])
    check(f"opencode2 stop: nothing left ({l})", not cmds("opencode2", l))
# Opt-out readback.
check("codex-opt: daemon_auto_start reads back false", RUNS["codex-opt"]["opt_out_readback"]["output"].split()[-1] == "false")
check("opencode2-opt: disabled reads back true", RUNS["opencode2-opt"]["opt_out_readback"]["output"].strip() == "true")
# Footprint.
check("codex: ~/.codex 434 MB in 142 files", round(mb("codex", ".codex")) == 434 and RUNS["codex"]["home_footprint"]["top_level_dirs"][".codex"]["files"] == 142)
check("codex-opt: ~/.codex 1.5 MB", round(mb("codex-opt", ".codex"), 1) == 1.5)
check("copilot: ~/.cache 212 MB", round(mb("copilot", ".cache")) == 212)
# No autostart entries or shell-rc changes in any run.
for run, r in sorted(RUNS.items()):
    fp = r["home_footprint"]
    check(f"{run}: no autostart path, .bashrc 3526 B, .profile 807 B",
          not any(fp["autostart_paths"].values()) and fp["shell_rc_bytes"][".bashrc"] == 3526 and fp["shell_rc_bytes"][".profile"] == 807)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
