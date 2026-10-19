# curl without NTLM: where it is already gone, and the failure that exits 0

Since curl 8.20.0 (April 29, 2026), NTLM is off unless whoever builds curl turns it on:
"Starting in curl 8.20.0, NTLM is disabled by default in the build unless specifically
enabled" ([curl blog](https://daniel.haxx.se/blog/2026/03/22/ntlm-and-smb-go-opt-in/)). curl's
[deprecation list](https://github.com/curl/curl/blob/master/docs/DEPRECATE.md) says NTLM
support "gets removed in September 2026". The pull request that removes it,
[curl/curl#22933](https://github.com/curl/curl/pull/22933), was still a draft on October 19.

On October 19 we checked 22 places people get curl from. **17 already ship curl 8.20 or
later without NTLM**, among them Debian testing and unstable, Alpine 3.24, Arch, Homebrew,
conda-forge and the official curl builds for Windows. Ubuntu 26.10, which we checked
separately, ships curl 8.20.0 without it too. Three of the 22 turned NTLM back on, and two
still ship a curl older than 8.20.

Asking for NTLM by name fails with an error. Letting curl pick the method does not: with
`--proxy-anyauth`, a curl without NTLM exits with code 0 and hands back the proxy's 407 page. PHP on the official `php:alpine`
image does the same thing with `curl_errno` 0.

## Check your curl

```sh
curl -V | grep -c NTLM
```

`0` means this curl has no NTLM. In PHP, this prints `false` when libcurl has no NTLM:

```php
$v = curl_version();
var_dump(($v['features'] & CURL_VERSION_NTLM) !== 0);
```

## Where curl ships without NTLM

Versions are as of October 19. "Installed" means we installed the distribution's own curl
package in its official container image and read `curl -V`. "Recipe" means we read the
packaging file the channel builds curl from.

| Where you get curl | curl | NTLM | Read from |
|---|---|---|---|
| Ubuntu 27.04 development (`ubuntu:devel`) | 8.20.0 | no | installed, recipe |
| Debian unstable (`debian:sid`) | 8.23.0 | no | installed, recipe |
| Debian testing | 8.22.0 | no | installed |
| Alpine 3.24 (`alpine:latest`) | 8.22.0 | no | installed, recipe |
| Alpine edge | 8.23.0 | no | installed, recipe |
| Arch Linux | 8.23.0 | no | installed, recipe |
| Wolfi | 8.23.0 | no, disabled explicitly | installed, recipe |
| `curlimages/curl` image | 8.23.0 | no | installed |
| nixpkgs unstable | 8.22.0 | no | recipe |
| Homebrew `curl` formula | 8.23.0 | no | recipe |
| MacPorts | 8.23.0 | no | recipe |
| MSYS2 (`mingw-w64-curl`) | 8.23.0 | no | recipe |
| conda-forge | 8.23.0 | no | recipe |
| vcpkg | 8.23.0 | no | recipe |
| Gentoo | 8.23.0 | no, disabled explicitly | recipe |
| Void Linux | 8.22.0 | no | recipe |
| curl for Windows (official binaries) | 8.23.0 | no | recipe |
| Fedora rawhide, full `curl` package | 8.23.0 | yes, turned back on | installed, recipe |
| openSUSE Tumbleweed | 8.23.0 | yes, turned back on | installed, recipe |
| Git for Windows | 8.23.0 | yes, turned back on | recipe |
| Fedora 44 | 8.18.0 | yes, older curl | installed |
| Rtools (R for Windows) | 8.1.2 | yes, older curl | recipe |

Outside those 22, Ubuntu 26.10 (`ubuntu:rolling`) has curl 8.20.0 without NTLM, and Ubuntu
26.04 LTS (`ubuntu:latest`) has curl 8.18.0 with NTLM. Both were installed and read the same
way.

Homebrew installs its curl next to the one that comes with macOS, so plain `curl` on a Mac
is still Apple's unless Homebrew's comes first on your `PATH`. We did not check Apple's curl.
Fedora's smaller `curl-minimal` package disables NTLM on purpose; the full `curl` package
keeps it.

## The failure that exits 0

We put curl behind a proxy that accepts only NTLM: squid with its `ntlm_fake_auth` helper,
which accepts any user name and password. It is a test stand-in, not a Windows server.

| Command | curl with NTLM | curl 8.23.0, default build |
|---|---|---|
| `curl -x <proxy> --proxy-ntlm -U u:p <url>` | exit 0, HTTP 200 | exit 2: `option --proxy-ntlm: the installed libcurl version does not support this` |
| `curl -x <proxy> --proxy-anyauth -U u:p <url>` | exit 0, HTTP 200 | **exit 0, HTTP 407** |

The `--proxy-ntlm` error does not mention that NTLM became a build option in 8.20. The
`--proxy-anyauth` request looks like success to any script that only checks the exit code.
Alpine 3.24's own curl package (8.22.0) gave the same results: exit 0 with HTTP 407 for
`--proxy-anyauth`, and exit 22 with `--fail`.

PHP behaves the same way. On the official `php:alpine` image (Alpine 3.24, PHP 8.5.11,
libcurl 8.22.0), `curl_setopt($ch, CURLOPT_PROXYAUTH, CURLAUTH_NTLM)` returned `false`.
`curl_exec` still sent the request, and the proxy answered 407. `curl_errno` was 0 and
`curl_error` was empty. With `CURLAUTH_ANY` the result was also 407 with `curl_errno` 0. The
same script on `php:latest` (Debian 13, libcurl 8.14.1) got 200 both ways.

## It has already broken things

- Git for Windows 2.55.0 (July 1) shipped libcurl 8.21.0 without NTLM. Users reported that
  pull and push with Windows domain accounts stopped working
  ([discussion #6307](https://github.com/git-for-windows/git/discussions/6307),
  [#6308](https://github.com/git-for-windows/git/issues/6308),
  [#6310](https://github.com/git-for-windows/git/issues/6310)). Its curl package turned NTLM
  back on the same day
  ([MINGW-packages#208](https://github.com/git-for-windows/MINGW-packages/pull/208)).
- A PHP user calling an on-premises Exchange API lost NTLM with a third-party Windows PHP
  build on curl 8.20 ([php/php-src#22157](https://github.com/php/php-src/issues/22157)).
  PHP's own Windows builds turn NTLM back on, and the third-party build was fixed.
- A user hit the `--ntlm` error on Kali Linux in September
  ([curl/curl#23134](https://github.com/curl/curl/issues/23134)); it was closed as a build
  issue.

## What to do

1. Run the check above wherever your scripts, containers and CI images get curl or libcurl.
2. In shell scripts, use `curl --fail` (`-f`). In our test with Alpine 3.24's curl 8.22.0 it
   turned the silent 407 into exit code 22. In PHP, check the return value of `curl_setopt`,
   and check the HTTP status, not only `curl_errno`.
3. If you still need NTLM, the options are:
   - Kerberos through HTTP Negotiate, if the proxy or server offers it: curl uses
     [`--proxy-negotiate`](https://github.com/curl/curl/blob/master/docs/cmdline-opts/proxy-negotiate.md)
     for a proxy and `--negotiate` for an origin server. We did not test either route. Every
     curl without NTLM that we installed lists Kerberos and SPNEGO in `curl -V`, except the
     two Alpine images, which list neither.
   - A local NTLM bridge such as [cntlm](https://cntlm.sourceforge.net/). Against our test
     proxy it worked with NTLMv1. Its NTLMv2 mode needs information our test proxy does not
     send, so we could not test NTLMv2.
   - A curl built with NTLM: Fedora's full `curl` package, openSUSE, or your own build with
     `--enable-ntlm` (autotools) or `-DCURL_ENABLE_NTLM=ON` (CMake). The planned removal
     would end this option.

## When the opt-in goes away

[#22933](https://github.com/curl/curl/pull/22933) removes NTLM support entirely. It is a
draft. curl adds features only in a window between releases. Under curl's
[release procedure](https://github.com/curl/curl/blob/master/docs/RELEASE-PROCEDURE.md), the
next window runs from about October 24 to November 14, and the next release is planned for
December 9. If the pull request merges in that window, that release would be the first
without NTLM for everyone, including builds that opt in today.

## How we tested

- We chose the 22 places before reading any of them. The list is not weighted by how many
  people use each one.
- 11 were installed in containers and 11 were read from their recipes only. Where we did
  both (8 channels), the recipe and the installed curl agreed.
- Controls: Debian 13's curl 8.14.1 lists NTLM. curl 8.23.0 built from the release tarball
  with default options does not; built with `--enable-ntlm`, it does.
- The proxy test ran in a Debian 13 container with squid 6.13, its `ntlm_fake_auth` helper
  and a local web server as the target. The PHP test ran the same script in the official
  `php:alpine` and `php:latest` images. The `--fail` test ran in an `alpine:3.24` container
  with Alpine's own curl and squid packages and the same fake helper.
- Each test ran once, on our own machine, on October 19. This is not an independent
  reproduction.

[`reproduce/`](reproduce/) has the `curl -V` output, the test scripts and their output, links
to each recipe at the exact commit we read (with its full SHA-256), and a script that checks
the census totals and the recorded test results. We read the recipes by hand; the same
script, run with `--fetch`, downloads the pinned recipes, checks their hashes and derives
each recipe's class again from the version and NTLM switches in them.

## Limits

- Images and recipes were read at their `latest` tags and branch heads on October 19. They
  change. The recipe links in `reproduce/` point at the commits we read; the images are not
  pinned.
- No user counts. The 22 channels are our choice.
- The test proxy is a stand-in that accepts any credentials, not Windows Server or Active
  Directory. Kerberos and an NTLMv2 bridge were not tested.
- Not checked: Apple's curl on macOS, the `curl.exe` that ships with Windows, and stable
  releases other than Debian 13, Alpine 3.24, Fedora 44 and Ubuntu 26.04.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai. We will publish dated corrections here.
