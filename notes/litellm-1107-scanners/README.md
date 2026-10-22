# litellm 1.107.0: trivy, grype and plain `pip-audit` still pass it (October 22)

LiteLLM [reports](https://docs.litellm.ai/blog/security-incident-oct-21-2026) that "a
malicious litellm==1.107.0 package was published to PyPI and was live for approximately 2
hours (11:39 UTC to 13:23 UTC)" on October 21, and that its Docker images `v1.107.0`,
`latest`, `main-latest` and `main-stable` "were compromised from 11:46 UTC to 14:20 UTC".

On October 22 between 07:52 and 08:09 UTC we gave four free scanners litellm 1.107.0 in a
`requirements.txt`, a `uv.lock`, a `poetry.lock` and an installed `dist-info` folder.
trivy 0.76.1 and grype 0.121.0 reported nothing in any of the four. `pip-audit` 2.10.1 with
its default settings printed "No known vulnerabilities found" and exited 0. osv-scanner 2.7.0
and `pip-audit -s osv` reported it as malware (MAL-2026-2144).

If your cleanup sweep uses trivy, grype or plain `pip-audit`, a pass does not clear
litellm 1.107.0 yet. Check for the version itself.

## Check for the version

In each Python environment:

```sh
pip show litellm
```

In a source tree:

```sh
grep -rnE 'litellm.*1\.107\.0' --include='requirements*.txt' .
grep -rn -A1 '^name = "litellm"' --include=uv.lock --include=poetry.lock . | grep '1\.107\.0'
```

On a disk or image:

```sh
find / -type d -name 'litellm-1.107.0.dist-info' 2>/dev/null
```

LiteLLM also says to search for `cook.pth` and `sitecustomize.py`, and that "not finding one
does not prove the environment is clean". None of the scanners below looks for those files:
they match package versions only.

If you want a scanner to do it:

- `pip-audit -s osv` reported MAL-2026-2144 for 1.107.0, both from `-r requirements.txt` and
  from `--path` pointed at a `site-packages` folder.
- `pip-audit --strict` exits 1 when it cannot check a package, so the deleted release fails the
  run instead of passing it. It also fails on any private package that is not on PyPI.
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
| `pip-audit` 2.10.1, default | skipped, exit 0 | not supported | not supported | skipped, exit 0 | skipped, exit 0 |
| `pip-audit` 2.10.1, `-s osv` | MAL-2026-2144 | not supported | not supported | MAL-2026-2144 | flagged |
| osv-scanner 2.7.0, `scan source` | MAL-2026-2144 | MAL-2026-2144 | MAL-2026-2144 | not read | flagged |

As controls, every scanner reported a known CVE for litellm 1.89.3 in each form it reads, so it
did read the file, and none reported malware for 1.106.2. We ran everything twice and got the
same result in every cell.

## Why they miss it

**`pip-audit` asks PyPI, and PyPI deleted the release.** By default `pip-audit` looks each
package up on PyPI. 1.107.0 is gone, so it skips litellm, prints "No known vulnerabilities
found" and exits 0. The skip is reported, as
`Dependency not found on PyPI and could not be audited: litellm (1.107.0)`, in a "Skip Reason"
table in the default output and as `skip_reason` in JSON, but a CI step that checks only the
exit code passes. The March malware, 1.82.7, was also deleted and gives the same result. With
the default service, `pip-audit` will not flag a malicious release once PyPI removes it.

**grype's database was built from GitHub data taken minutes too early.** grype does read
GitHub's malware advisories: it flagged 1.82.7 with GHSA-92x9-889m-jgmw. GitHub added 1.107.0 to
that advisory at 00:32:04 UTC on October 22. The grype database we used took its GitHub data at
00:29:32 UTC, two and a half minutes earlier. We expect the next database to flag it, and will
check on October 23.

**trivy reported only the reviewed advisory.** trivy flagged 1.82.7 through
GHSA-5mg7-485q-xm76, GitHub's reviewed advisory for the March releases, whose range is still
">= 1.82.7, <= 1.82.8". It did not report the malware advisory for any version we tested. We do
not expect trivy to flag 1.107.0 until GitHub adds it to a reviewed advisory.

## Public repositories show little exposure

In public GitHub pull requests that mention 1.107.0, we found 4 repositories that ran CI on a
change to 1.107.0 while it was on PyPI: 3 automated update pull requests and 1 opened by a
person. None came from Dependabot or Renovate. No public dependency file we found still pins
1.107.0. On October 22 the compromised Docker image digest returned 404 on both GHCR and Docker
Hub, and `latest` pointed at 1.106.2. We are not naming the repositories.

The exposure that matters is private: unpinned `pip install litellm` and `docker pull` of
`latest` during the window. Code search cannot count those.

## How we tested

- **Inputs.** Synthetic files only: `litellm==V` in `requirements.txt`, minimal `uv.lock` and
  `poetry.lock` entries, and a `litellm-V.dist-info` folder with a three-line `METADATA` and no
  code, for V = 1.107.0, 1.82.7, 1.89.3 and 1.106.2. We downloaded no package or image from the
  compromised release.
- **Scanners.** trivy (`fs`, and `rootfs` for the installed folder), grype (`dir:`),
  osv-scanner (`scan source -r`) and `pip-audit` (`-r --no-deps --disable-pip`, and `--path`)
  in their official images, pinned by digest, except `pip-audit`, which we installed from PyPI
  into the official Python image. Each scanner downloaded its own database at run time.
- **Runs.** Two complete runs on October 22, 07:52–08:09 UTC, with identical results.
- **Exposure count.** At about 07:40 UTC on October 22 we searched GitHub for pull requests
  matching `litellm 1.107.0 is:pr` (234 results) and read the start times of the CI checks on
  those opened between 11:39 and 13:23 UTC on October 21. For pins we searched code for
  `"litellm==1.107.0"` and for 1.107.0 in `uv.lock` and `poetry.lock`, and read each file at
  its default branch. Search results are capped, so these are lower bounds.
- We ran this once, ourselves. Nobody has reproduced it independently.

[`reproduce/`](reproduce/) has the input generator, the run script, the scorer, both runs' raw
output and the scored results.

## Limits

- One reading of databases that change daily. trivy and grype will update; the date is part of
  every result above.
- Version matching only. No scanner here looks for `cook.pth` or other files the malware leaves.
- We did not test GitHub Dependabot alerts or commercial scanners.
- Public code search cannot see private repositories, unpinned installs or image pulls.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai. We will publish dated corrections here.
