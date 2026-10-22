# Reproduce: `macos-latest` and OpenSSL 4

Everything here uses made-up keys, certificates and passwords.

## Run it on a macOS runner

Copy `macos-openssl4.yml` to `.github/workflows/` in a repository of your own, copy
`probe.sh`, `tls_check.py` and `signing-step.sh` to a `reproduce/` folder in the same
repository, and run the workflow from the Actions tab. `probe.sh` prints the image, which
OpenSSL each path points at, the version-check table, the `-legacy` reads, `version -e` and
`version -m`, the `security import` results and the key-identifier table. To run the signing
step as well, add a second step: `run: bash reproduce/signing-step.sh`.

After November 8 the default `openssl` on these images should be 4.x. The scripts call
openssl@3, openssl@4 and `/usr/bin/openssl` by path, so the tables should not change unless
the installed versions do.

## Raw output

- `results/probe-macos-latest.txt` and `results/probe-macos-26.txt`: `probe.sh` on
  GitHub-hosted runners on October 22, 2026 (macOS 26.6.2, image 20261013.0424.1). We ran an
  earlier copy of `probe.sh` that differed only in where it looked for `tls_check.py`.
- `results/signing-step-macos-latest.txt`: `signing-step.sh` on the same image.
- `results/linux-python-check.txt`: the key-identifier check with Python 3.13.16 against
  OpenSSL 3.6.5 and 4.0.3 builds on Linux.
- `results/replay-summary.json`: totals from the replay of 2,202 workflow calls. The list of
  repositories and calls is not published.

## Check the note

```sh
python3 check.py
```

It reads the raw output and checks every row of the note's tables and the replay totals. It
exits 0 when they all match and 1 when one does not.
