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

Third-party material and its licenses: [THIRD-PARTY.md](THIRD-PARTY.md).
