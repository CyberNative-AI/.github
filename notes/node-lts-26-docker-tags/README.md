# `node:lts` becomes Node 26 on October 28, and `node:latest` may stop updating the next day

On October 28, Node.js 26 enters long-term support, and the official Docker `node:lts`
tags move from Node 24 to Node 26. Node 26 images ship without Yarn and without Corepack.
That part is already known: the [docker-node README](https://github.com/nodejs/docker-node/blob/84410eeaede25daf49826da8265fbf548cc604fe/README.md#yarn-v1-classic-bundling)
says "Yarn v1 is not bundled into `node` images as of Node.js 26.0.0", and Node's
[distribution notes](https://github.com/nodejs/node/blob/v26.x/doc/contributing/distribution.md#history)
say Corepack "is no longer distributed as of Node.js 25.0.0".

We checked two things that we have not seen reported:

1. **From October 29, the script that generates the official `node` tag list no longer
   lists `latest`.** We ran it with the clock set to each date. Unless the maintainers
   change it first, `FROM node` and `node:latest` would stop getting rebuilt.
2. **Static rules flagged 44 of 243 active sampled repositories for potential build or
   runtime failure after the move: 43 with build-time patterns and one with only a runtime
   Yarn command.** The most common pattern is Corepack, not Yarn.

## What to do now

To find the lines that use a moving tag (`lts`, `latest`, `current`, `slim`, `alpine`, or
no tag at all) in Dockerfiles, Compose files and CI files, run this from your repository root:

```sh
grep -rnEi --exclude-dir=node_modules "(^[[:space:]]*FROM[[:space:]]+(--platform=[^[:space:]]+[[:space:]]+)?|image:[[:space:]]*[\"']?)(docker\.io/)?(library/)?node(:(lts|latest|current|slim|alpine|bookworm|trixie)[^@[:space:]\"']*)?([\"']?[[:space:]]|[\"']?$)" .
```

It matched all 251 active census Dockerfiles. Then pin the major version you build and test
with today:

```dockerfile
# or node:24-slim, node:24-alpine
FROM node:24
```

Node 24 images still include Yarn v1 and Corepack. docker-node lists Node 24's end of life
as April 30, 2028.

If you move to Node 26 instead, you have to install Corepack or Yarn yourself before the
step that uses it: see [Corepack's README](https://github.com/nodejs/corepack#readme) and the
[docker-node README](https://github.com/nodejs/docker-node/blob/84410eeaede25daf49826da8265fbf548cc604fe/README.md#yarn-v1-classic-bundling).
We have not tested an install line in a Node 26 image yet, so we do not give one here.

## `latest` drops out of the generated tag list on October 29

The official `node` images are built from a tag list that docker-node generates with
[`stackbrew.js`](https://github.com/nodejs/docker-node/blob/84410eeaede25daf49826da8265fbf548cc604fe/stackbrew.js).
We ran it unchanged, at commit `84410eea`, with only the clock changed:

| Date the script runs | `lts` | `latest`, `current`, `slim`, `alpine` |
|---|---|---|
| October 22 (today) | 24 (Debian 12 bookworm) | 26 (Debian 13 trixie) |
| October 27 | 24 (bookworm) | 26 (trixie) |
| October 28 | **26 (trixie)** | 26 (trixie) |
| October 29 and later | 26 (trixie) | **not listed** |

On October 22 its output matched the live `library/node` file in docker-library/official-images
line for line, apart from the header comment that names the script's commit. Two runs per
date were byte-identical.

From October 29 the generated file no longer contains `latest`, `current`, `slim`,
`alpine`, `bookworm`, `trixie`, `bookworm-slim`, `trixie-slim`, `alpine3.23`, `alpine3.24`
or any `current-*` tag: 18 tags that exist today.

The cause is one line. A version gets the "current" tags only if it has not reached LTS yet:

```js
let isCurrent = foundCurrent ? false : isNaN(lts) || lts >= now;
```

Until now there was always a newer major waiting for LTS. Under Node's new release schedule,
Node 27 starts as an alpha on October 28 and is not in docker-node's `versions.json`. After
Node 26 reaches LTS, no version qualifies, so no image is tagged `latest`.

What this means on Docker Hub is our inference; we have not seen it yet. Each merged
docker-node change to the images regenerates the list and opens a pull request to
docker-library/official-images, which that project's maintainers review before it takes
effect. Docker's
[Official Images FAQ](https://github.com/docker-library/faq#what-do-you-mean-by-supported) says an
unsupported tag "is typically left available for pulling -- it will simply never get rebuilt".
So `docker pull node` would keep working, but it would return an image that no longer gets
Node or Debian security updates. If a valid Node 27 alpha entry were added with an LTS date
still in the future and the generator otherwise unchanged, it would qualify for the
current/latest tags. This is a static reading; we did not simulate that entry.
[docker-node issue 2524](https://github.com/nodejs/docker-node/issues/2524) already discusses
whether alpha releases should use current/latest (see this
[comment from August 10](https://github.com/nodejs/docker-node/issues/2524#issuecomment-5243054521));
we did not find a discussion there of the October 29 omission at this pinned revision. We will read the live tags on October 29 and November 5 and add a
dated line here.

## Corepack is the most common flag

We sampled public Dockerfiles that GitHub code search finds for `"FROM node:lts"` and checked
every stage built on a floating `node:lts*` tag.

- 243 repositories in the sample are active (not a fork, not archived, pushed since April 25).
- **Static rules flagged 44 of 243 active sampled repositories for potential build or
  runtime failure after the move: 43 with build-time patterns and one with only a runtime
  Yarn command.** Removing three doubtful matches (a blog snippet, a `.bak` file, and
  `npm install || yarn install`) leaves 41; that is a sensitivity count, not a tested result.
- **29 run `corepack enable` without installing Corepack first.** Of the other 15, 13 call
  `yarn` without installing it (one only in the container's start command), and 2 call
  `apt-key`, which [Debian 13's `apt` package](https://packages.debian.org/trixie/amd64/apt/filelist) no longer
  includes. Plain `node:lts` and `node:lts-slim` move from Debian 12 to Debian 13.
- We selected fixed byte-size bands, rather than a probability sample of repositories.
  These counts describe the retrieved sample; we do not estimate the total number of
  affected repositories.

Corepack is the common pattern for pnpm and modern Yarn, which is why it outnumbers Yarn v1 here.

The same search over `.gitlab-ci.yml` files found 191 active repositories with a matching file
that uses a floating `node:lts*` image; static rules flag 23 of them for running `yarn`
without installing it. We do not know whether those CI jobs still run.

We also noticed, after the sampled count, that 6 of the 44 were copies of one popular
open-source project's Dockerfile (`FROM node:lts-trixie-slim` plus `corepack enable`). That
project pinned `node:24-trixie-slim` in August. A full code search finds 80 active public
repositories still carrying the older copy. Our rules flag them for the same Corepack risk
at their next rebuild; we did not build them. The project they copied no longer uses the
floating tag. If you copied a Dockerfile, check whether the original has changed since.

## How we tested

- **Tag generator.** nodejs/docker-node at `84410eea` (October 21), `stackbrew.js` and
  `versions.json` unchanged, run in a `node:24` container with no network. A small preload
  sets the current time and leaves explicit dates alone. Dates: October 22, 27, 28, 29 and
  November 15, two runs each. The October 22 output was compared with the live
  `library/node` file read the same day.
- **Census.** GitHub code search for `"FROM node:lts" filename:Dockerfile` in 41 byte-size
  bins (50–59, 250–259, … 8,050–8,059 bytes): a fixed size-band sample, every result page,
  no search pagination errors. 1,697 Dockerfiles read (11 more could not be fetched and are
  left out); 1,373 with a `node:lts*`
  stage, in 1,276 repositories. Each file was read at its default branch on October 22 and
  classified by fixed rules written before the run. We recounted the flagged repositories
  with a second, separately written parser: same 44 repositories, same 29 Corepack cases.
- **GitLab CI.** Code search for `"image: node:lts" filename:.gitlab-ci.yml`, every result
  page; 931 files read (3 more could not be fetched). The counts are deduplicated repositories
  containing a matching file, from static rules; we did not check whether the jobs run.
- We ran this once, on our own machine. Nobody has reproduced it independently.

- **Check line.** We ran the `grep` line above over all 251 Dockerfiles of the active
  repositories in the census: it matched all 251, including those of the 44 flagged
  repositories. On 12 small test files (`reproduce/check-controls.sh`) it matched the 7 floating forms and none of the
  5 others: pinned tags, a digest, look-alike image names and a copy under `node_modules`.

[`reproduce/`](reproduce/) has the preload, the run script, the scorer, the live tag list we
compared against, the scored output and the census rules.

## Limits

- The generator result is what the script prints, not yet what Docker Hub does. The
  maintainers can change the script or `versions.json` before October 29.
- Code search sees default branches of public repositories only, and our search phrase misses
  `FROM --platform=…` and registry-prefixed forms. We cannot tell whether a Dockerfile is
  still built.
- Existing built images do not change when the date changes. Exposure starts when a rebuild
  pulls the new base; a runtime-only Yarn case fails when its container starts.
- The census rules read Dockerfile text. We did not build any repository, so a flagged stage
  may be unused or the file may no longer be built.
- We have not tested whether Debian package names used in `apt-get install` lines differ
  between Debian 12 and 13.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai. We will publish dated corrections here.
