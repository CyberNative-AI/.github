# About 1 in 50 recent dotfiles that set PATH add a literal `~` entry

*CyberNative AI LLC · Sample collected October 12, 2026*

This line is common in shell startup files:

```sh
export PATH="$PATH:~/.local/bin"
```

The quotes stop the shell from expanding `~`, so PATH gets the entry `~/.local/bin` as written. That is a relative path. [disconnect3d's post](https://disconnect3d.pl/2026/10/02/dont-put-tilde-in-your-path/) (October 2) shows what follows: a program that searches PATH can look in `./~/.local/bin` under whatever directory it is running in. We measured how often public dotfiles do this, tested what common shells, runtimes and build tools then run, and checked whether ShellCheck catches it.

## Check yours

```sh
echo "$PATH" | tr : '\n' | grep '~'
```

This is the check from disconnect3d's post. Any output is a literal entry. To fix it, write `$HOME` instead of `~` in the startup file:

```sh
export PATH="$PATH:$HOME/.local/bin"
```

## How often

We ran seven GitHub searches for non-fork repositories named `dotfiles`, one for each day from October 4 to 10, 2026, and took 72 repositories from one random results page per day: 504 in total. 289 of them set PATH in a shell startup file outside vendored plugins. We ran each simple PATH statement in its own shell (bash or zsh) in an offline container and read the resulting PATH. Statements with command substitution, pipes or redirections were scanned instead of run.

- **6 of 289** (2.1%, 95% CI 0.95–4.45%) leave a literal `~` entry: about 1 in 50.
- 2 of 289 put it before `/usr/bin`.
- Among the 500 most-starred `dotfiles` repositories, 10 of the 299 that set PATH do (3.3%, about 1 in 30), and 5 of 299 put it before `/usr/bin`.

One more repository has spaces after the colons, like the synthetic example `PATH="…: ~/a: ~/b"`. Those entries start with a space rather than `~`, so we did not count them. They are relative paths containing a space, rather than home-directory paths. Counting it gives 7 of 289, still about 1 in 50.

## What each tool runs

We put the literal entry `~/.local/bin` in PATH and placed a program with the same name in both `$HOME/.local/bin` and `./~/.local/bin` under the current directory.

| Finds or runs the `$HOME` copy | Finds or runs the copy under the current directory | Refuses |
|---|---|---|
| bash 5.2 in its default mode; Ruby 3.3 `system`, backticks and `IO.popen` | `bash --posix`, dash, busybox sh, zsh 5.9, fish 4.0, `env`, Python 3.13 `subprocess.run` and `shutil.which`, Node 20 `spawnSync`, GNU make, git external subcommands, `xargs`, `find -exec`, Perl `system` | Go 1.25 `exec.Command` (`ErrDot`) |

Bash expands the entry for its own lookups, so in an interactive bash session the line seems to work. Most other tools resolve it against their current directory. If the entry comes last in PATH, those tools reach it only for names not found earlier, such as the tools you installed in `~/.local/bin`. If it comes first, it shadows everything: `ls` started from Python's `subprocess` or `sh -c` ran a `./~/.local/bin/ls` inside the directory, while bash and Ruby ran `/usr/bin/ls`.

To see it on Debian or Ubuntu with `/bin/dash`, `/bin/bash` and `/usr/bin/python3` installed, paste this. It uses a clean environment, creates one small script in a new temporary directory, and leaves that directory for inspection. It stops if the temporary directory cannot be created or entered.

```sh
/usr/bin/env -i PATH=/usr/bin:/bin /bin/bash --noprofile --norc <<'DEMO'
demo_dir=$(mktemp -d) || exit 1
cd "$demo_dir" || exit 1
export HOME="$PWD/home"
mkdir -p "$HOME" '~/.local/bin' || exit 1
printf '#!/bin/sh\necho "ran ./~/.local/bin/cn_tilde_demo in $PWD"\n' > '~/.local/bin/cn_tilde_demo' || exit 1
chmod +x '~/.local/bin/cn_tilde_demo' || exit 1
PATH="$PATH:~/.local/bin" /bin/dash -c cn_tilde_demo
PATH="$PATH:~/.local/bin" /usr/bin/python3 -I -c 'import subprocess; subprocess.run(["cn_tilde_demo"])'
PATH="$PATH:~/.local/bin" /bin/bash --noprofile --norc -c cn_tilde_demo
DEMO
```

The dash and Python commands print the temporary directory. Bash looks in the empty temporary home directory instead and reports `command not found` (exit status 127).

## Agents, CI and sandboxes

Coding agents, CI jobs and editor tasks often run inside a repository someone else wrote, and they often start tools through Python, Node, `sh -c` or make rather than an interactive bash. If the PATH they inherit has a literal `~` entry, a directory named `~` in that repository becomes part of the search path. Our test shows the mechanism, not an incident: we have no evidence that anyone has placed such a directory to exploit it. A sandbox that copies the user's PATH copies the entry too. disconnect3d found theirs when an agent sandbox reported it as a writable PATH entry.

## ShellCheck misses the common form

ShellCheck has a rule for this, SC2147, but it checks only plain assignments. Its SC2088 warning fires when a quoted value starts with `~`, not when `~` follows a colon:

```sh
PATH="$PATH:~/a"             # SC2147
export PATH="$PATH:~/b"      # nothing
declare -x PATH="$PATH:~/c"  # nothing
export PATH="~/d:$PATH"      # SC2088
```

ShellCheck 0.10.0, 0.11.0 and master build v0.11.0-120-g98deabe gave the same result in our October 12, 2026 tests. On the 21 literal PATH lines we found across our samples, ShellCheck 0.10.0 flagged the 11 where the tilde starts the quoted value. It missed the other 10, all with the tilde after a colon in an `export` argument. We reported this upstream: https://github.com/koalaman/shellcheck/issues/3559.

## What this does not show

- That these lines run on real machines. A line can sit inside a condition or in a file that is never loaded, or a later line can reset PATH. One of the 6 is in a backup copy of a zsh startup file that is probably not loaded; without it, the count is 5 of 288.
- That anyone has placed a `~` directory to exploit this. We have no evidence of that.
- Anything beyond public GitHub repositories named `dotfiles`. zsh user options and fish configuration files were not modelled.
- Independent reproduction. This is an internal execution and internal rerun, not independently reproduced. A second run inside our company, on the same machine, reproduced every output byte for byte and recloned 60 repositories; nobody outside the company has repeated it.

## How we checked

- Before reading any prevalence result, we replaced a first sample from a single day, whose repositories had all been pushed within about 5.5 hours, with the week-long sample above. That single-day sample gives 2 of 288.
- Counts are per repository. We do not name repositories or users or publish their lines, because a line can be found by search.
- The tool test ran in a Debian trixie container without network access: bash 5.2.37, dash 0.5.12, busybox 1.37, zsh 5.9, fish 4.0.2, Python 3.13, Node 20.19, GNU make 4.4.1, git 2.47, Perl 5.40, Ruby 3.3.12 and Go 1.25.3. Results were the same with the entry first or last, except for the `ls` shadowing described above.
- ShellCheck has no zsh mode, so zsh files were checked with `-s bash`.

Published by CyberNative AI LLC. AI systems collected the sample, ran the tests and the internal rerun, and wrote this note. Corrections: hello@cybernative.ai.
