# Evidence for "What 9 coding-agent CLIs leave running after you close the window"

Process-level evidence for the note in the parent directory: 13 runs executed once each on
our own machine on 2026-10-18. Status: executed, not independently reproduced.

## Files

| file | contents |
|---|---|
| `runs/<run>.json` | one file per run: tool, version, configuration, whether the client exited before its window closed, every non-harness process alive at each check (pid, parent pid, session id, state, command line), stop-command output, opt-out readback, sizes of top-level entries in `$HOME`, autostart paths and shell-rc sizes |
| `summary.csv` | one row per run: what was alive 10 s after window A, 10 s and 330 s after window B, 330 s after the stop command, and the largest entry written in `$HOME` |
| `check.py` | recomputes the note's process, stop, opt-out and footprint statements from `runs/` (Python 3, standard library; prints PASS/FAIL, exits 1 on any mismatch) |
| `Dockerfile` | the image recipe the runs used (only its first comment line differs) |
| `SHA256SUMS` | hashes of the files above |

Run the check:

```sh
python3 check.py
```

This bundle holds the process-level evidence for the note. It does not include the driver
script, the terminal recordings or the stand-in tool used by the two control runs. The
per-run files were extracted from our raw result files; fields the note does not use were
left out.

## What each run did

One fresh container per run from the `Dockerfile` image: `docker run --rm --init --network
none --user 1500 --cpus 2 --memory 4g`. The configured runtime limit was 1,500 seconds for
four runs and 1,200 seconds for the remaining nine; all 13 finished within 1,200 seconds.
`$HOME` held only the image's
default shell files and, for some tools, a config file that skips first-run prompts. Each
tool got a synthetic API key. With no network no model could answer, so only the tool's own
`!` shell mode was exercised.

1. Session A: start the tool in a pseudo-terminal in `~/proj-a`, run one `!` shell command,
   quit with the tool's exit command, then close the terminal (hang-up to the session).
2. List processes 10 s later.
3. Session B: the same in `~/proj-b`.
4. List processes 10, 60, 180 and 330 s after B closed. Record `$HOME` sizes, autostart
   paths (`~/.config/autostart`, `~/.config/systemd/user`) and the sizes of `~/.bashrc` and
   `~/.profile`.
5. `codex` and `opencode2` runs only: after the 330-second post-B check, run the stop
   command, then list processes 10, 60 and 330 seconds later.

| tool | run | started with | quit with | stop command / opt-out |
|---|---|---|---|---|
| Codex CLI 0.163.0 | `codex` | `codex` (after `codex login --with-api-key`) | `/quit` | `codex app-server daemon stop` |
| Codex CLI 0.163.0 | `codex-opt` | same | `/quit` | `~/.codex/config.toml`: `[features]` `daemon_auto_start = false`, set before session A |
| OpenCode 2.0.32 | `opencode2` | `opencode` | `/exit` | `opencode service stop` |
| OpenCode 2.0.32 | `opencode2-opt` | `opencode` | `/exit` | `opencode service set disabled true`, set before session A |
| OpenCode 1.19.3 | `opencode1` | `opencode1` (link to the 1.19.3 package's `opencode`) | `/exit` | |
| Claude Code 2.1.302 | `claude` | `claude` | `/exit` | |
| Gemini CLI 0.64.0 | `gemini` | `gemini` | `/quit` | |
| Qwen Code 0.25.2 | `qwen` | `qwen` | `/quit` | |
| Crush 0.98.1 | `crush` | `crush` | Ctrl+C | |
| Kilo CLI 7.8.12 | `kilo` | `kilo` | `/exit` | |
| GitHub Copilot CLI 1.0.98 | `copilot` | `copilot` (folder-trust prompt accepted) | `/exit` | |
| stand-in | `ctl-daemon` | a stub that leaves a detached process | `/exit` | |
| stand-in | `ctl-plain` | a stub that leaves nothing | `/exit` | |

## Check it yourself

A by-hand version of the Codex observation (not the harness we ran):

```sh
docker build -t cli-leftovers .
docker run --rm -it --init --network none cli-leftovers bash
# inside the container
export OPENAI_API_KEY=sk-not-a-real-key
printenv OPENAI_API_KEY | codex login --with-api-key
mkdir -p ~/proj-a && cd ~/proj-a && codex     # accept the trust prompt, type !pwd, then /quit
ps -eo pid,ppid,sid,args | grep '[c]odex'     # app-server --managed-daemon and pid-update-loop
codex app-server daemon stop
sleep 60; ps -eo pid,ppid,sid,args | grep '[c]odex'   # pid-update-loop still listed in our run
```

The same steps with `opencode` and `opencode service stop` cover OpenCode 2.0.32.

## Limits

Versions as listed. One execution per run on our own machine. No network, so update checks
failed. Linux container with no systemd user session and no desktop. Only the user's `!`
shell mode, not model tool calls. Sessions ran one after the other. The base image is
pinned by tag (`node:24.22.0-slim`), not by digest.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai.
