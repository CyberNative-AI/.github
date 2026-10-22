# litellm 1.107.0: trivy, grype and plain `pip-audit` still pass it (October 22)

LiteLLM [reports](https://docs.litellm.ai/blog/security-incident-oct-21-2026) that "a
malicious litellm==1.107.0 package was published to PyPI and was live for approximately 2
hours (11:39 UTC to 13:23 UTC)" on October 21, and that its Docker images `v1.107.0`,
`latest`, `main-latest` and `main-stable` "were compromised from 11:46 UTC to 14:20 UTC".

On October 22 between 07:52 and 08:09 UTC we gave four free scanners litellm 1.107.0 in a
`requirements.txt`, a `uv.lock`, a `poetry.lock` and an installed `dist-info` folder.
trivy 0.76.1 and grype 0.121.0 reported nothing in any of the four. `pip-audit` 2.10.1 with
its default PyPI service printed "No known vulnerabilities found" and exited 0. osv-scanner 2.7.0
and `pip-audit -s osv` reported it as malware (MAL-2026-2144).

If your cleanup sweep uses trivy, grype or plain `pip-audit`, a pass does not clear
litellm 1.107.0 yet. Check for the version itself.

## Check for the version

Do not start Python or `pip` on a machine, virtual environment or image that may have
installed 1.107.0, not even for `pip show`. LiteLLM's
[incident report](https://docs.litellm.ai/blog/security-incident-oct-21-2026) warns that "any
Python start in the affected environment runs `cook.pth` and `sitecustomize.py` again", "and
that includes running pip". Look at the files instead, preferably from a clean machine with the
suspect disk or image mounted read-only.

In a source tree:

```sh
grep -rnE 'litellm.*1\.107\.0' --include='requirements*.txt' .
grep -rn -A1 '^name = "litellm"' --include=uv.lock --include=poetry.lock . | grep '1\.107\.0'
```

On a disk or image mounted read-only, here at `/mnt/suspect`:

```sh
find /mnt/suspect -type d -name 'litellm-1.107.0.dist-info' 2>/dev/null
```

LiteLLM also says to search for `cook.pth` and `sitecustomize.py`, and that "not finding one
does not prove the environment is clean". None of the scanners below looks for those files:
they match package versions only. If 1.107.0 was ever installed, follow the report's "What to
do if you are affected" steps; no scanner result replaces them.

If you want a scanner to check, run it on a clean machine against copies of your dependency
files or of the `*.dist-info` metadata folders, never inside a suspect environment:

- `pip-audit -s osv` reported MAL-2026-2144 for 1.107.0, both from `-r requirements.txt` and
  from `--path` pointed at a folder holding only `litellm-1.107.0.dist-info` metadata, with no
  package code.
- `pip-audit --strict` exits 1 when it cannot audit a package, according to pip-audit 2.10.1's
  source, so the skipped release fails the run instead of passing it. It also fails on any
  private package that is not on PyPI.
- `osv-scanner scan source -r .` reported MAL-2026-2144 from all three files. It does not read
  installed packages. For `requirements.txt` it also resolves dependencies of dependencies, so
  a failing exit code alone does not mean malware: read the IDs.
- GitHub's advisory API lists the malware advisory only when you ask for that type:
  `gh api '/advisories?ecosystem=pip&affects=litellm@1.107.0&type=malware'` returns
  GHSA-92x9-889m-jgmw; without `&type=malware` it returns nothing.

## What each scanner reported

| Scanner (database) | `requirements.txt` | `uv.lock` | `poetry.lock` | installed | 1.82.7 (March malware) |
|---|---|---|---|---|---|
| trivy 0.76.1 (DB updated Oct 22 01:15Z) | clean | clean | clean | clean | flagged |
| grype 0.121.0 (DB built Oct 22 06:29Z) | clean | clean | clean | clean | flagged |
| `pip-audit` 2.10.1, default PyPI service | skipped, exit 0 | not supported | not supported | skipped, exit 0 | skipped, exit 0 |
| `pip-audit` 2.10.1, `-s osv` | MAL-2026-2144 | not supported | not supported | MAL-2026-2144 | flagged |
| osv-scanner 2.7.0, `scan source` | MAL-2026-2144 | MAL-2026-2144 | MAL-2026-2144 | not read | flagged |

As controls, every scanner reported a known CVE for litellm 1.89.3 in each form it reads, so it
did read the file, and none reported malware for 1.106.2. We ran everything twice and got the
same result in every cell.

## Why they miss it

**`pip-audit`'s default service asks PyPI, and PyPI deleted the release.** By default
`pip-audit` looks each package up on PyPI. PyPI answered 404 for 1.107.0, so `pip-audit` skipped
litellm, printed "No known vulnerabilities found" and exited 0. It reported the skip as
`Dependency not found on PyPI and could not be audited: litellm (1.107.0)` in the JSON
`skip_reason`, and its source shows the same reason in a "Skip Reason" table in the default
output, but a CI step that checks only the exit code passes. The March malware, 1.82.7, was
also deleted and gave the same result. What we observed is this case: when its PyPI service gets
a 404 for a version, `pip-audit` skips that package.

**grype's database may predate the 1.107.0 entry.** grype does read GitHub's malware
advisories: it flagged 1.82.7 with GHSA-92x9-889m-jgmw. On October 22 GitHub's API listed 1.107.0
in that advisory, with a last update time of 00:32:04 UTC. The grype database we used took its
GitHub data at 00:29:32 UTC, two and a half minutes earlier. That fits a database built just
before 1.107.0 was added, but the update time does not show what changed, and we have not seen
the advisory's earlier version. We will check a newer grype database on October 23.

**trivy reported only the reviewed advisory.** trivy flagged 1.82.7 through
GHSA-5mg7-485q-xm76, GitHub's reviewed advisory for the March releases, whose range is still
">= 1.82.7, <= 1.82.8". It did not report the malware advisory for any version we tested. We do
not expect trivy to flag 1.107.0 until GitHub adds it to a reviewed advisory.

## How we tested

- **Inputs.** Synthetic files only: `litellm==V` in `requirements.txt`, minimal `uv.lock` and
  `poetry.lock` entries, and a `litellm-V.dist-info` folder with a three-line `METADATA` and no
  code, for V = 1.107.0, 1.82.7, 1.89.3 and 1.106.2. We downloaded no package or image from the
  compromised release.
- **Scanners.** trivy (`fs`, and `rootfs` for the installed folder), grype (`dir:`),
  osv-scanner (`scan source -r`) and `pip-audit` (`-r --no-deps --disable-pip -f json`, and
  `--path -f json`) in their official images, pinned by digest, except `pip-audit`, which we
  installed from PyPI into the official Python image. Each scanner downloaded its own database
  at run time.
- **Runs.** Two complete runs on October 22, 07:52–08:09 UTC, with identical results.
- **`pip-audit` table output and `--strict`.** Our recorded `pip-audit` runs used JSON output.
  The "Skip Reason" table and the exit 1 under `--strict` come from reading pip-audit 2.10.1's
  source ([command line](https://github.com/pypa/pip-audit/blob/v2.10.1/pip_audit/_cli.py),
  [columns](https://github.com/pypa/pip-audit/blob/v2.10.1/pip_audit/_format/columns.py),
  [PyPI service](https://github.com/pypa/pip-audit/blob/v2.10.1/pip_audit/_service/pypi.py)),
  not from a recorded run.
- We ran this once, ourselves. Nobody has reproduced it independently.

[`reproduce/`](reproduce/) has the input generator, the run script, the scorer, both runs' raw
output and the scored results. The raw output contains third-party advisory data; see
[`reproduce/THIRD-PARTY-DATA.md`](reproduce/THIRD-PARTY-DATA.md).

## Limits

- One reading of databases that change daily. trivy and grype will update; the date is part of
  every result above.
- Version matching only. No scanner here looks for `cook.pth` or other files the malware leaves.
- We did not test GitHub Dependabot alerts or commercial scanners.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai. We will publish dated corrections here.
