# GitHub has switched `openssl` to 4.x on `macos-latest` (Arm64). A `'^OpenSSL 3'` check drops `-legacy`

**Update, 21 November 2026.** GitHub has finished deploying the macOS 26 Arm64 image that
makes OpenSSL 4.1.0 the default `openssl`. The Xcode 27 Arm64 image with the same change is
still rolling out, so a GitHub Actions job on Xcode 27 Arm64 can get either default. The
[revised schedule](https://github.com/actions/runner-images/issues/14856) targeted November 2–15,
subject to compatibility validation.

In a GitHub Actions job on a macOS 26 or Xcode 27 Arm64 image, run `openssl version` before
changing `PATH` to see what the job gets. If the job needs OpenSSL 3, call it directly as
`"$(brew --prefix openssl@3)/bin/openssl"`. The new images list OpenSSL 3.5.9 at
`/opt/homebrew/opt/openssl@3/bin/openssl`.

GitHub [merged the build change](https://github.com/actions/runner-images/pull/15285)
on November 10. The release notes for macOS 26 Arm64
[20261112.0504](https://github.com/actions/runner-images/releases/tag/macos-26-arm64/20261112.0504)
and [20261117.0516](https://github.com/actions/runner-images/releases/tag/macos-26-arm64/20261117.0516)
(published November 13 and 18) and Xcode 27 Arm64
[20261119.0378](https://github.com/actions/runner-images/releases/tag/xcode-27-arm64/20261119.0378)
(published November 19) show the default moving from 3.5.9 to 4.1.0. All three were
still marked as pre-releases on November 19. By November 21, GitHub had converted macOS 26 Arm64
20261117.0516 to a release. In [GitHub's release process](https://github.com/actions/runner-images#image-releases),
a pre-release means deployment has started, and the conversion to a release means it has
finished. Xcode 27 Arm64 20261119.0378 was still a pre-release on November 21. The
[latest macOS 26 Intel image](https://github.com/actions/runner-images/releases/tag/macos-26/20260824.0517)
was published in August. We ran no hosted jobs for this update, so we have no measure
of how many jobs get the new default. The tests below used OpenSSL 4.0.3.

**Update, 9 November 2026.** The switch has not happened. The software lists for the newest images,
macOS 26 Arm64 [20261102.0473](https://github.com/actions/runner-images/releases/tag/macos-26-arm64/20261102.0473)
(published 3 November) and Xcode 27 Arm64 [20261104.0337](https://github.com/actions/runner-images/releases/tag/xcode-27-arm64/20261104.0337)
(published 4 November), still give OpenSSL 3.5.9 as the default `openssl`, with OpenSSL 4.1.0
installed alongside it at `/opt/homebrew/opt/openssl@4/bin/openssl`. GitHub's
[image build script](https://github.com/actions/runner-images/blob/741e4eb8ef5f51698d730ac16ede65cadb067522/images/macos/scripts/build/install-openssl.sh)
still sets OpenSSL 3 as the default on macOS 26, and the
[announcement](https://github.com/actions/runner-images/issues/14856) is still open with no new
date. It says the rollout is "subject to compatibility validation". To select OpenSSL 4 explicitly
on those images, put `/opt/homebrew/opt/openssl@4/bin` first on `PATH`. Our tests below used
OpenSSL 4.0.3, the 4.x on the image in October.

GitHub [announced](https://github.com/actions/runner-images/issues/14856) the switch from
OpenSSL 3.x to 4.x on October 6 for macOS 26 Intel, macOS 26 Arm64 and Xcode 27 Arm64.
Its original rollout window was November 2–8, 2026. On GitHub Actions, `macos-latest` uses
the macOS 26 Arm64 image.

We found 2,202 calls to plain `openssl` in jobs on these runners in 1,027 active public
repositories, and ran 2,031 of them under OpenSSL 3.5.9, 3.6.5 and 4.0.3 with the same
inputs. 1,825 behaved the same. Of the rest, we expect three repositories to have a step that
fails or quietly changes, and in two of them the cause is a version check the workflow
makes itself: `openssl version | grep '^OpenSSL 3'`, written to tell Homebrew's OpenSSL 3
from the LibreSSL that macOS ships as `/usr/bin/openssl`. With OpenSSL 4 that check is
false, so the workflow stops passing `-legacy`. OpenSSL 4 still needs it.

## Check your workflows

```sh
grep -rnE "\^OpenSSL 3|openssl version -e" .github/ scripts/
```

Also look for `x509 -req -CA` with `-extfile` (see [below](#ca-signed-certificates-lose-their-key-identifiers)).

## The check that drops `-legacy`

This is the pattern, as it appears in Apple code-signing steps:

```sh
LEGACY_FLAG=""
if openssl version 2>/dev/null | grep -q '^OpenSSL 3'; then
  LEGACY_FLAG="-legacy"
fi
openssl pkcs12 -in certificate.p12 -out cert.pem -clcerts -nokeys $LEGACY_FLAG -passin pass:"$P12_PASSWORD"
```

We ran it on a GitHub-hosted macOS 26 runner (macOS 26.6.2, image 20261013.0424.1) with a
throwaway `.p12` in the old RC2-40-CBC format that the workflows' own comments say Apple
Developer exports use. Both OpenSSL versions are already installed on that image, so we put
each one first on `PATH`:

| `openssl` on `PATH` | `grep '^OpenSSL 3'` | `grep '^OpenSSL [3-9]'` |
|---|---|---|
| OpenSSL 3.6.5 (the default on October 22) | `-legacy` added, read works | `-legacy` added, read works |
| OpenSSL 4.0.3 (the 4.x we tested) | **no `-legacy`, read exits 1** | `-legacy` added, read works |
| LibreSSL 3.3.6 (`/usr/bin/openssl`) | no flag, read works | no flag, read works |

The OpenSSL 4 failure reads:

```
Error outputting keys and certificates
...:error:0308010C:digital envelope routines:inner_evp_generic_fetch:unsupported:crypto/evp/evp_fetch.c:376:Global default library context, Algorithm (RC2-40-CBC : 0), Properties (<null>)
```

We also ran a typical signing step end to end under `bash -e`, as Actions runs it: read the
`.p12`, export it again with 3DES and a SHA-1 MAC, and `security import` it into a new
keychain. With `'^OpenSSL 3'` on OpenSSL 4.0.3 it stopped at the first read and imported
nothing; with `'^OpenSSL [3-9]'` it imported the identity on all three.

### If the check guards an export

When the same check decides `pkcs12 -export -legacy`, OpenSSL 4 writes the file without
`-legacy`: AES-256-CBC with PBKDF2 and a SHA-256 MAC. On the same runner, `security import`
refused that file with this message, although the password was right:

```
security: SecKeychainItemImport: MAC verification failed during PKCS12 import (wrong password?)
```

It refused an OpenSSL 3.6.5 export without `-legacy` the same way, and imported the
`-legacy` export. The legacy formats here are a workaround for the importer tested on this
runner, not a recommendation for protecting new PKCS#12 files.

## `openssl version -e` is gone

OpenSSL 4 removed engines. `openssl version -e` prints `version: Unknown option: -e` and
exits 1. In a line like
`echo $(openssl version -e | sed …) >> "$GITHUB_ENV"`, the step still succeeds and the
variable is never set. One workflow we found used it to build a library path for its tests.
`openssl version -m` prints `MODULESDIR` on both 3.6.5 and 4.0.3; its parent is the `lib`
directory that `ENGINESDIR` pointed into.

## CA-signed certificates lose their key identifiers

OpenSSL 4 no longer adds Subject and Authority Key Identifiers to a certificate signed with
`openssl x509 -req -CA ca.crt -CAkey ca.key -extfile san.cnf` unless the file asks for them.
Python 3.13 and later check certificates strictly by default and reject such a server
certificate when the CA has a `keyUsage` extension:

| Server certificate signed by | Key identifiers | Python client (`ssl.create_default_context`) |
|---|---|---|
| OpenSSL 3.6.5, `-extfile` with only `subjectAltName` | both | handshake works |
| OpenSSL 4.0.3, same command | none | **fails: `Missing Authority Key Identifier`** |
| OpenSSL 4.0.3, two lines added (below) | both | handshake works |

That was Python 3.15.0 on the macOS runner; on Linux, Python 3.13.16 gave the same result.
Add these two lines to the extensions file:

```
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid,issuer
```

None of the repositories we found combined all three conditions (a CA with `keyUsage`, an
extensions file with only the SAN, and a strict client), so this is a how-to, not a count.

## Output that changed, and greps that still match

- `-text` dumps drop the leading `00:` byte of an RSA modulus and print 16 bytes per hex row
  instead of 15.
- EC keys print `Private-Key: (256 bit field, 128 bit security level)` instead of
  `Private-Key: (256 bit)`.
- The `Subject:`, `Issuer:`, `ASN1 OID:` and `NIST CURVE:` lines are unchanged, and
  `grep '^OpenSSL'` still matches `openssl version`.

## Headers and libraries are already OpenSSL 4

On the image we ran, `openssl` was 3.6.5, but Homebrew's shared `include/openssl`,
`lib/libssl.dylib` and `pkg-config --modversion openssl` all pointed at OpenSSL 4.0.3, and the
runner's `python3` (3.15.0) reported OpenSSL 4.0.3. A native build that found OpenSSL through
those paths built against 4.0.3 on that image. The rollout changes the default command. We
did not check which paths individual build tools use.

## What to do

1. Run the `grep` above on every workflow and script that runs on `macos-latest`,
   `macos-26` or Xcode 27 images.
2. If you need OpenSSL 3 on a GitHub Actions macOS 26 or Xcode 27 Arm64 image, call it by its
   prefix as shown in the update above. It printed 3.6.5 on the image we tested. The November
   Arm64 images linked above list OpenSSL 3.5.9.
3. If you only need to tell OpenSSL from LibreSSL, match `'^OpenSSL [3-9]'` rather than
   `'^OpenSSL 3'`.
4. Keep `-legacy` when OpenSSL 4 reads an old `.p12`, and when you export one for
   `security import`.
5. Replace `openssl version -e`. Add the two key-identifier lines to any extensions file you
   sign server certificates with.

## How we tested

- **Finding the calls.** On October 22 we ran 32 GitHub code searches and got 3,908
  workflow files. 1,027 repositories that are public, not archived and pushed to since
  April 21 have 2,202 plain `openssl` calls in jobs on `macos-latest`, `macos-26` or Xcode 27
  labels. Code search caps its results, so these are lower bounds. Only `run:` lines were
  read.
- **Replaying them.** Each call ran with the same synthetic keys, certificates and files
  under vanilla OpenSSL 3.5.9, 3.6.5 and 4.0.3, built on Linux with Homebrew's configure
  options. A call counted as changed only if 4.0.3 differed from both 3.x versions. 2,031 of
  2,202 calls (92%) could be run: 1,825 were the same, 139 printed something different (103
  of them `openssl version` itself), 66 wrote a different file, and 1 failed
  (`openssl version -e`). We then read every changed call in its workflow. We are not naming
  the three repositories here.
- **On macOS.** The tables above come from GitHub-hosted `macos-latest` and `macos-26`
  runners on October 22 (both macOS 26.6.2, image 20261013.0424.1, Apple silicon), with
  Homebrew's openssl@3 3.6.5 and openssl@4 4.0.3 and the system LibreSSL 3.3.6. Both labels
  gave the same results. All certificates and passwords were made up for the test.
- Each test ran once, by us. This is not an independent reproduction.

[`reproduce/`](reproduce/) has the macOS workflow and scripts, their raw output, the
replay totals, and `check.py`, which checks the raw output against the results in this
note's tables and the replay totals. It does not read this page; we compared the page with
the raw output separately.

## Limits

- The replay ran Linux builds of OpenSSL, not Homebrew's macOS bottles. The macOS runs cover
  the claims in the tables, not all 2,031 calls.
- Only workflow `run:` lines: not the scripts they call, composite actions, private
  repositories or self-hosted runners.
- We used a synthetic RC2-40 `.p12`, not an Apple Developer export, and stopped at
  `security import`: no `codesign` or notarization.
- We tested the image on October 22. The updates above describe GitHub’s rollout as of November 9 and 21.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai. We will publish dated corrections here.
