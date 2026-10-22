# Reproduce

## Tag generator

```sh
sh run-generator.sh WORKDIR          # clones nodejs/docker-node, checks out 84410eea, runs it 10 times
python3 score.py WORKDIR library-node-live-20261022.txt
```

`fakedate.js` sets the time that `new Date()` returns; nothing in docker-node is changed.
`generated/` holds our outputs for October 22, 27, 28, 29 and November 15, two runs each.
`library-node-live-20261022.txt` is the live `library/node` file from
docker-library/official-images, read on October 22. `generator-scores.json` is `score.py`
run on `generated/`:

```sh
python3 score.py generated library-node-live-20261022.txt | cmp - generator-scores.json
```

To check the one-line cause yourself, read `isCurrent` in
[`stackbrew.js`](https://github.com/nodejs/docker-node/blob/84410eeaede25daf49826da8265fbf548cc604fe/stackbrew.js)
against the `lts` dates in
[`versions.json`](https://github.com/nodejs/docker-node/blob/84410eeaede25daf49826da8265fbf548cc604fe/versions.json).

## Check line

`sh check-controls.sh` writes the 12 test files to a temporary folder and runs the note's
`grep` line on them: 7 matches, `a` to `g`.

## Census

`census-rules.py` holds the rules we used to decide which Dockerfile stages use a floating
`node:lts*` tag and which of them the rules flag as at risk on Node 26. `census-summary.json` has the counts.
We do not publish the list of repositories.

## Install lines

`install-lines/images.txt` lists the six images by digest. `install-lines/probe.sh` runs one
test group inside an image: `G1` lists the tools the image includes, `G2` is a plain
`npm install --global yarn`, `G3` the Yarn v1 line from the note and `G4` the Corepack line.
From the `install-lines` folder, for each image and group:

```sh
docker run --rm -e G=G4 -e TAG=26-trixie -e REP=1 -v "$PWD:/src:ro" -v "$PWD/out:/work" \
  node@sha256:a98e6fda54fdbb22d4238054cca9a2a113bcd1191c09193a535aae22f400aa8e sh /src/probe.sh
```

Each run writes `out/TAG/G-rREP.rc` (exit code per step; 0 is success, 127 is "command not
found") and a `.log` with the output. `install-lines/runs/` holds ours, and
`install-lines/results.json` collects their exit codes.

## Debian package lists

`install-lines/apt/lists-full.txt` and `lists-slim.txt` hold the 21 distinct package lists
from the active census Dockerfiles, one per line under an opaque ID, plus a control (`ctl1`)
and one named package (`probe1`). `apt-replay.sh` runs `apt-get update` and then a simulated
install of each list. From the `install-lines/apt` folder:

```sh
docker run --rm -e TAG=26-trixie -e VARIANT=full -v "$PWD:/src:ro" -v "$PWD:/in:ro" \
  -v "$PWD/out:/work" \
  node@sha256:a98e6fda54fdbb22d4238054cca9a2a113bcd1191c09193a535aae22f400aa8e sh /src/apt-replay.sh
```

Use the `24-bookworm` image for Debian 12, and the `-slim` images with `VARIANT=slim`.
`results/` holds our output: one line per list with its exit code (0 resolved, 100 failed)
and the first error lines.

Third-party material and its licenses: [THIRD-PARTY.md](THIRD-PARTY.md).
