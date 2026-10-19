# Evidence for "curl without NTLM: where it is already gone, and the failure that exits 0"

Everything here was executed once on our own machine on 2026-10-19. Status: executed, not
independently reproduced.

## Files

| file | contents |
|---|---|
| `census.csv` | the 22 channels plus Ubuntu 26.10 and 26.04: class, curl version, the image installed (if any), the recipe at the commit we read and its full SHA-256, and the NTLM flag found in the recipe |
| `recipe-sources.csv` | every recipe and companion file we read on October 19 (version files such as `meta.yaml`, `vcpkg.json` and Debian changelogs): a link to it at a fixed commit and the full SHA-256 of the bytes we captured. Each link was checked to serve exactly those bytes. One row, curl-for-win's `_versions.sh`, was not part of the October 19 read: we located it afterwards, at the commit that was the branch head when we read `curl.sh` |
| `runtime/<name>.txt` | output of `runtime-check.sh` for each image: package versions, `/etc/os-release` lines and `curl -V` after installing the image's own curl package. `c-plus-debian-trixie.txt` is the Debian 13 control |
| `runtime-check.sh` | installs curl in each image and records `curl -V`. Versions in `census.csv` are the package versions; Wolfi's `curl -V` reports `8.23.0-DEV` for its package `curl-8.23.0-r0` |
| `proxy-test.sh`, `proxy-test.txt` | builds curl 8.23.0 from the release tarball twice (default, `--enable-ntlm`) in `debian:trixie`, starts squid with `ntlm_fake_auth` as an NTLM-only proxy, and runs the curl commands in the note; `TAG` lines are the results |
| `cntlm-ntlmv1.sh`, `cntlm-ntlmv1.txt` | the same proxy with cntlm in NTLMv1 mode in front of it (run after the NTLMv2 attempt in `proxy-test.txt` failed against the fake helper) |
| `php-test.sh`, `php-alpine.txt`, `php-latest.txt` | the PHP script from the note, run in the official `php:alpine` and `php:latest` images |
| `fail-test.sh`, `fail-test.txt` | Alpine 3.24's own curl and squid packages: `--proxy-anyauth` with and without `--fail` |
| `check.py` | checks the census totals and the recorded runtime and test results from the files above, and that every recipe class has a pinned source. Python 3, standard library; prints PASS/FAIL, exits 1 on any mismatch. We classified the recipes by hand; `python3 check.py --fetch` also downloads each pinned recipe, verifies its SHA-256 and derives the recipe's class again (older than 8.20: OLD; an NTLM enable switch: KEPT; otherwise DROPPED) |
| `SHA256SUMS` | hashes of the files above |

```sh
python3 check.py           # offline
python3 check.py --fetch   # also downloads and checks the pinned recipes
```

## Rerunning

`runtime-check.sh` needs Bash and Docker, and it overwrites `runtime/`, so run it in a copy
of this directory. The other `.sh` files run inside a fresh container of the named image:

```sh
bash runtime-check.sh
docker run --rm -v "$PWD":/w:ro --entrypoint sh debian:trixie /w/proxy-test.sh
docker run --rm -v "$PWD":/w:ro --entrypoint sh debian:trixie /w/cntlm-ntlmv1.sh
docker run --rm -v "$PWD":/w:ro --entrypoint sh php:alpine /w/php-test.sh
docker run --rm -v "$PWD":/w:ro --entrypoint sh alpine:3.24 /w/fail-test.sh
```

`cntlm-ntlmv1.sh` defines paths to two curl builds it does not use; only Debian 13's own curl runs in it.
Images move: a rerun reads whatever the `latest` tags hold that day.

## Changes from what we ran

- We ran the containers through a local job queue. Its status lines are removed from the
  `.txt` files; nothing else in them is changed.
- `runtime-check.sh` calls `docker run` directly where we called that queue with the same
  arguments (`--rm --cpus 2 --memory 2g`).
- The recipes are not copied here. `recipe-sources.csv` links each one at the commit that
  served the bytes we read and gives their full SHA-256. On October 19 we fetched them from
  branch heads; the commit links were found afterwards by matching those hashes.

The 22 channels, the classes and the controls were written down before any recipe or image
was read. The PHP and `--fail` tests were added afterwards.
