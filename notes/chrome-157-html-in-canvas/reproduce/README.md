# Reproduce

Everything behind the note's tables, as it ran on October 23.

- `pages/`: the test pages. `K0` (nothing to draw) and `K1`–`K3` (plain 2D, WebGL and WebGPU
  drawing) are the negative and positive controls. `N2D`, `NGL`, `NGPU` use the new names. `B2D`,
  `BGL`, `BGPU` are the three rendering snippets from Chrome's May post, with the element's size
  and colour, a `requestPaint()` call, our probe and, where a snippet leaves it out, the context
  setup and a draw added. `T3`, `T3PR`, `PC`, `BJS`, `BJSN`, `PX` are the
  engines. `BJSW` and `BJSW2` are the Babylon.js `update()` pages, added after the main run.
  `probe.js` records which API names exist, the `paint` events and each engine's feature checks.
- `run.mjs`, `run_all.sh`: the runner. It serves `pages/` and the engine files on localhost,
  starts each browser with a fresh profile over the DevTools protocol, records exceptions,
  console messages and the probe, and screenshots the canvas at 4 and 7 seconds.
- `score.py`: counts magenta pixels in each screenshot (at least 4,000 = renders, under 400 =
  blank) and combines them with the exceptions.
- `assets.json`: sha256 of every Chrome for Testing build, npm tarball and the pull request
  archive (three.js pull request 34732 at `b28067fa`).
- `results/main/`: the main run, 16 pages x 4 browsers x 2 loads: one JSON line per load, every
  screenshot, and `score.json`.
- `results/babylon-update/`: the Babylon.js `update()` run, with `K0`, `K1` and `BJS` repeated
  as controls.
- `census/`: `census_summary.json` (counts by class), `old-names-only.json` (the 143
  repositories and their matched files), `head_recheck.jsonl` (the named repositories' matched
  files re-read at their default branch on October 23). The counts come from the text of the
  files GitHub's code search returned, not from parsing code. The search scripts are not
  included.
- `LICENSE-Apache-2.0.txt`: the license of the Chrome blog code samples that `B2D`, `BGL`,
  `BGPU`, `N2D`, `NGL`, `NGPU`, `PC`, `T3` and `T3PR` adapt. Each of those pages starts with a
  comment naming its source and our changes.

## Run it

You need the three Chrome for Testing builds (156.0.8078.47, 157.0.8103.15, 158.0.8119.0, Linux
x64) under `bin-cft/<version>/chrome-linux64/`, and the npm tarballs listed in `assets.json`
unpacked under `assets/<name>-<version>/package/` (three.js pull request 34732 under
`assets/pr34732/`). Check them against `assets.json` first.

We ran each group of browsers in one container: image `mcr.microsoft.com/playwright:v1.62.1-noble`,
4 CPUs, 6 GB memory, no network, all capabilities dropped, a non-root user, 1 GB shared memory and
a 2 GB `/tmp`. Mounts: `bin-cft` at `/bin-cft`, `assets` at `/assets`, `pages` at `/work/pages`
and the folder holding `run.mjs` and `run_all.sh` at `/work/src`, all read-only, and an empty,
writable output folder at `/out`. Inside the container:

```sh
ARMS="C156 C156OT C157 C158" sh /work/src/run_all.sh 2 K0 K1 K2 K3 N2D NGL NGPU B2D BGL BGPU T3 T3PR PC BJS BJSN PX
```

`C156OT` is 156 with `--enable-blink-features=CanvasDrawElement`. Then, outside:

```sh
python3 score.py <output folder> > score.json
python3 score.py results/main > /dev/null   # prints the main table from our records
```

After the run we changed only comments and descriptions: the source and license notices at the
top of the adapted pages, the first line of `probe.js`, `run.mjs`, `run_all.sh` and `score.py`,
and the census list's file name and `note` text.
