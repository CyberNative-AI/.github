# On Windows, uninstalling your last uv tool deleted your uv.toml

uv 0.13.1 (October 14, 2026) fixes [astral-sh/uv#22491](https://github.com/astral-sh/uv/issues/22491). When `uv tool uninstall` removes the last installed tool, older releases also delete the folder that holds the tools directory, as long as that folder has no other subdirectories. Files in it do not count. On Windows that folder is `%APPDATA%\uv`, which is also where the user config `uv.toml` lives. uv prints only `Uninstalled 1 executable: <name>`.

Every release we tested deletes it, from 0.3.0 (August 20, 2024, when `uv tool` became stable) to 0.13.0. 0.13.1 keeps it.

| uv | Config after uninstalling the last tool |
|---|---|
| 0.3.0, 0.4.0, 0.5.0, 0.6.0, 0.8.0, 0.10.0, 0.12.0, 0.13.0 | deleted, with the whole folder |
| 0.13.1 | kept |

## If the file set your index, uv goes back to PyPI

With `[pip] index-url = "https://example.invalid/simple"` in the user `uv.toml`, `uv pip compile` fails on `example.invalid` before the uninstall. After the uninstall, the same command resolves `cowsay==6.1` from PyPI, with no warning (`results/run-0.13.0.log`). Every other setting in the file is gone too. Project `pyproject.toml` and `uv.toml` files and `UV_*` environment variables are not touched.

## Check (PowerShell)

```powershell
uv --version
uv tool dir
Test-Path "$env:APPDATA\uv\uv.toml"
```

You were exposed if `uv tool dir` prints `...\AppData\Roaming\uv\tools`, you kept a user `uv.toml` there, and you removed your last tool while `%APPDATA%\uv` had no other subfolder. A uv-managed Python (`python\`) or saved credentials (`credentials\`) folder kept it safe. If `%APPDATA%\uv\data` exists, uv keeps tools there instead, and the deleted folder did not hold your config.

If the file is missing, restore it from your backup or dotfiles, then upgrade uv to 0.13.1 or later (`uv self update` for the standalone installer) before you uninstall another tool.

On macOS and Linux the default config (`~/.config/uv`) and tools (`~/.local/share/uv/tools`) are in different folders. There you are affected only if the folder above the tools directory holds files you keep and no other subdirectories, for example through `UV_TOOL_DIR`, or with `XDG_DATA_HOME` and `XDG_CONFIG_HOME` set to the same folder.

## Method and limits

- Linux x86-64, uv installed from PyPI. `scripts/repro.sh <version>` gives uv the Windows layout with `XDG_CONFIG_HOME=<root>` and `UV_TOOL_DIR=<root>/uv/tools`, so the config and the tools directory share one folder. It needs any uv on `PATH` to fetch the tested version. Output is in `results/`.
- **Not run on Windows.** The Windows paths come from the uv source at 0.3.0 and 0.13.0 (`crates/uv-state`, `crates/uv-dirs`, `crates/uv-settings`) and the reporter's PowerShell run in #22491.
- We tested the eight releases in the table and 0.13.1, not every release between them or the earlier preview releases of `uv tool`.
- `uv python uninstall` had similar cleanup code, which 0.13.1 also changes. In our run of `scripts/repro-python.sh`, removing the last managed Python on 0.13.0 left the config in place. We did not look further.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai.
