# What 9 coding-agent CLIs leave running after you close the window

Since 0.157.0, an interactive Codex CLI session starts a background server that outlives the
window ([openai/codex#48195](https://github.com/openai/codex/issues/48195)). OpenCode 2.0
now starts a shared background service by default too. We wanted to know which other
coding-agent CLIs do this. On October 18 we ran the same test on nine of them: start a
session, run one shell command, quit and close the terminal, do the same again in a second
project directory, then list every process still alive 10, 60, 180 and 330 seconds later.

**Two of the nine left a background process running: Codex CLI 0.163.0 and OpenCode
2.0.32. The other seven left nothing.** Both tools have a setting that prevents it: with it set
before the first session, nothing was left running. Codex's stop command did not stop everything.

| Tool | Version | Still running 330 s after the second window closed | Largest directory written in `$HOME` |
|---|---|---|---|
| Codex CLI | 0.163.0 | `codex app-server --managed-daemon` and `codex app-server daemon pid-update-loop` | `~/.codex`, 434 MB |
| OpenCode | 2.0.32 (`@opencode/cli`) | `opencode.exe serve --service` | `~/.local`, 0.27 MB |
| OpenCode | 1.19.3 (`opencode-ai`) | nothing | `~/.local`, 0.85 MB |
| Claude Code | 2.1.302 | nothing | `~/.claude`, 0.79 MB |
| Gemini CLI | 0.64.0 | nothing (see below: slow to exit) | `~/.gemini`, under 0.01 MB |
| Qwen Code | 0.25.2 | nothing | `~/.qwen`, under 0.01 MB |
| Crush | 0.98.1 | nothing | 0.36 MB in each project directory |
| Kilo CLI | 7.8.12 | nothing | `~/.local`, 0.96 MB |
| GitHub Copilot CLI | 1.0.98 | nothing | `~/.cache`, 212 MB |

## Codex CLI 0.163.0

After the first session, two processes were running with parent PID 1, each in its own
session: `codex app-server --managed-daemon` and an updater, `codex app-server daemon
pid-update-loop`. Both were still alive 330 seconds after the second window closed.

After two short sessions `~/.codex` held 434 MB in 142 files. #48195 describes most of this
as a copy of the installed Codex package (about 374 MB there) that the server runs from.

**Opt-out: works.** With this in `~/.codex/config.toml` on a fresh install, nothing was left
running at any check and `~/.codex` was 1.5 MB after both sessions:

```toml
[features]
daemon_auto_start = false
```

**Stop command: incomplete.** `codex app-server daemon stop` returned `"status":"stopped"`
and the server exited, but the `pid-update-loop` updater was still running 10, 60 and 330
seconds later. #48195 reported the same on 0.157.0. We tested the opt-out setting on a fresh install only,
not on a machine where the server was already running. For that case #48195 gives a
workaround that also kills the updater and removes the package copy.

## OpenCode 2.0.32

After the first session, a process running `opencode.exe serve --service` stayed alive with
no window open, through the 330-second check.

**Opt-out: works.** After `opencode service set disabled true`, nothing was left at any
check.

**Stop command: works.** After `opencode service stop`, nothing was running at 10, 60 or
330 seconds.

We tested the CLI only. [anomalyco/opencode#55861](https://github.com/anomalyco/opencode/issues/55861)
reports that the desktop app ignores the disabled setting.

## Gemini CLI 0.64.0: slow to exit, not a daemon

After `/quit`, Gemini CLI did not exit. It was still alive 10 seconds after each terminal
closed. After session B, it was gone by the 60-second check; we did not take that check
after session A. It started nothing else. We tested only `/quit` followed by closing the
terminal.

## What we did not find

No tool wrote a systemd user unit or an autostart entry, and the sizes of `~/.bashrc` and
`~/.profile` were unchanged. The test container had no systemd user session and no desktop, so a tool that
installs these only when they exist would not show up here.

## How we tested

- One fresh Docker container per run (no network, 2 CPUs, 4 GB) with a fresh home
  directory and a synthetic API key. Every run finished within 20 minutes. Without a
  network no model answered, so the test exercises the tools' own shell mode (`!`), not
  commands the model runs.
- Each tool ran in a pseudo-terminal. Session A started in `~/proj-a`, ran one `!` shell
  command, quit with the tool's own exit
  command (`/quit` or `/exit`; Ctrl+C for Crush) and then closed the terminal. Session B did
  the same in `~/proj-b`. We listed every process at 10, 60, 180 and 330 seconds after B
  closed and recorded the size of each top-level directory in `$HOME`.
- In the Codex and OpenCode 2 runs we then ran the tool's stop command and listed processes
  again 10, 60 and 330 seconds later. Separate runs tested both tools with the opt-out set
  before the first session.
- Two control runs used a stand-in tool, one that leaves a background process and one that
  does not, to check that the test detects both. Both came out as expected.
- Results were scored by a script fixed before the runs. A second scoring script, written
  by a separate AI agent from only the written protocol and the raw output, agreed on every
  result in all 13 runs.

Per-run process listings, stop-command output and home-directory sizes, with a script that
rechecks the statements above, are in [`reproduce/`](reproduce/).

## Limits

- Results apply to the versions listed. Claude Code has since released 2.1.303; the other
  eight were still the current npm releases on October 19.
- Each configuration ran once on our own machine. This is not an independent reproduction.
- No network, so update checks failed. Codex's updater could not download anything. Online
  behavior may differ.
- Linux container only, with no systemd user session and no desktop apps. Desktop apps and
  editor extensions were not tested.
- Only the user's `!` shell mode was tested, not model tool calls. Sessions ran one after
  the other, not at the same time.

## Related reports

- [openai/codex#48195](https://github.com/openai/codex/issues/48195): asks for
  `daemon_auto_start` to be opt-in; documents the server, the package copy, the updater and
  the stop-command gap on 0.157.0.
- [openai/codex#51961](https://github.com/openai/codex/issues/51961): a Homebrew install of
  0.160.0 starting the server and updater from a separate 0.161.0 package.
- [openai/codex#52067](https://github.com/openai/codex/issues/52067): the server's releases
  directory keeps every old release and grew to 2.8 GB.
- [openai/codex#53547](https://github.com/openai/codex/issues/53547): a user report on
  0.162.1 that the server picks up the environment variables of the first session that
  started it, and that later, unrelated sessions can see them.
- [anomalyco/opencode#52891](https://github.com/anomalyco/opencode/issues/52891),
  [#55228](https://github.com/anomalyco/opencode/issues/55228) and
  [#55861](https://github.com/anomalyco/opencode/issues/55861): environment and lifecycle
  reports for the OpenCode 2 background service.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai. We will publish dated corrections here.
