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
- `pages-babylon-9.33.0/` and `results/babylon-9.33.0/`: the October 29 rerun of `BJS` and `BJSW`
  on Babylon.js 9.33.0. The two pages differ from `pages/` only in the Babylon script path; `K0`
  and `K1` from `pages/` ran as controls.
- `pages-three-0.187.0/` and `results/three-0.187.0/`: the October 30 rerun of `T3` on three.js
  0.187.0. The page differs from `pages/T3.html` only in the three.js path; `K0` and `K1` from
  `pages/` ran as controls.
- `pages-pixijs-dev/` and `results/pixijs-dev/`: the October 30 run of PixiJS's merged fix, npm
  `pixi.js@8.22.0-dev.4fabfa6`. `PR` (WebGL) and `PRGPU` (WebGPU) put the element directly in the
  canvas; `PRN` and `PRGPUN` nest it one level. They load the build from `assets/pixi.js-pr12341/`,
  the path we first used for the fix's pull-request build. `PX` from `pages/` and `PXGPU` (8.22.0
  with WebGPU) ran as controls; this run had no `K0`/`K1` pages.
- `results/stable-157.0.8103.38/`: the November 3 rerun of the 16 main-run pages from `pages/`,
  unchanged, on Chrome for Testing 157.0.8103.38, the build Linux Stable served from November 3.
  The arm keeps the label `C157`; each record's `browser` field names the build.
- `pages-playcanvas-2.24.0/` and `results/playcanvas-2.24.0/`: the November 10 run of PlayCanvas
  2.24.0. `PB` (WebGL2) and `PBGPU` (WebGPU) mark the canvas `content="drawable"` and the element
  `drawable`; `PBOLD` keeps the old `layoutsubtree` markup. `PC` from `pages/` (2.23.3) ran as the
  control. The arm `C157S` is Chrome for Testing 157.0.8103.38. Our runner for this run also
  accepts a device scale factor; at its default of 1 it does what `run.mjs` here does, and its
  records carry an extra `dpr` field. The same run also covered a scale factor of 2 and a
  four-colour version of each page; those cells agreed with these and are not included.
- `results/pixijs-8.23.0/`: the November 12 run of PixiJS 8.23.0, the first release with the
  fix, on the pages in `pages-pixijs-dev/`, unchanged, with `PX` from `pages/` and `PXGPU`
  (8.22.0) as controls. The arm `C157S` is Chrome for Testing 157.0.8103.38. As in the November
  10 run, the runner accepted a device scale factor, here left at 1, and the records carry a
  `dpr` field.
- `census/`: `census_summary.json` (counts by class), `old-names-only.json` (the 143
  repositories and their matched files), `head_recheck.jsonl` (the named repositories' matched
  files re-read at their default branch on October 23). The counts come from the text of the
  files GitHub's code search returned, not from parsing code. The search scripts are not
  included.
  `head_recheck_20261103.jsonl` is the November 3 re-read of all 407 matched files of the 143
  repositories at their default branch, made by `head_recheck_20261103.py` with the same text
  rules (`python3 -I head_recheck_20261103.py old-names-only.json out.jsonl` prints the counts).
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

For the October 29 rerun, copy `pages-babylon-9.33.0/BJS.html` and `BJSW.html` over the ones in
`pages/`, unpack `babylonjs-9.33.0` under `assets/` as above, and run
`ARMS="C156 C156OT C157 C158" sh /work/src/run_all.sh 2 K0 K1 BJS BJSW`;
`python3 score.py results/babylon-9.33.0 > /dev/null` prints its table from our records.

For the October 30 three.js rerun, copy `pages-three-0.187.0/T3.html` over `pages/T3.html`, unpack
`three-0.187.0` under `assets/`, and run `ARMS="C156 C156OT C157 C158" sh /work/src/run_all.sh 2 K0 K1 T3`.
For the PixiJS run, copy `pages-pixijs-dev/*.html` into `pages/`, unpack `pixi.js-8.22.0-dev.4fabfa6`
as `assets/pixi.js-pr12341/package/`, and run
`ARMS="C156 C156OT C157 C158" sh /work/src/run_all.sh 2 PX PXGPU PR PRGPU PRN PRGPUN`.
`python3 score.py results/three-0.187.0 > /dev/null` and `python3 score.py results/pixijs-dev > /dev/null`
print their tables from our records; we regenerated both `score.json` files with this `score.py`.
For the November 3 Stable run, add Chrome for Testing 157.0.8103.38 under
`bin-cft/157.0.8103.38/chrome-linux64/` (its zip is in `assets.json`) and run, in the same container,
`node /work/src/run.mjs /bin-cft/157.0.8103.38/chrome-linux64/chrome C157 /work/pages /assets /out 2 K0 K1 K2 K3 N2D NGL NGPU B2D BGL BGPU T3 T3PR PC BJS BJSN PX`.
That is what `run_all.sh` does for `C157`, with this build in place of 157.0.8103.15.
`python3 score.py results/stable-157.0.8103.38 > /dev/null` prints its table from our records.
For the November 10 PlayCanvas run, copy `pages-playcanvas-2.24.0/*.html` into `pages/`, unpack
`playcanvas-2.24.0` under `assets/`, and run `ARMS="C156 C156OT C157 C158" sh /work/src/run_all.sh 2 PC PB PBOLD PBGPU`,
then `node /work/src/run.mjs /bin-cft/157.0.8103.38/chrome-linux64/chrome C157S /work/pages /assets /out 2 PC PB PBOLD PBGPU`.
`python3 score.py results/playcanvas-2.24.0 > results/playcanvas-2.24.0/score.json` prints its table from our
records and regenerates our `score.json` byte for byte. The table has no column for the 157.0.8103.38 arm
(`C157S`); its cells are in `score.json`.
For the November 12 PixiJS run, set up `pages/` as for the October 30 PixiJS run, unpack
`pixi.js-8.23.0` as `assets/pixi.js-pr12341/package/`, and run
`ARMS="C156 C156OT C157 C158" sh /work/src/run_all.sh 2 PX PXGPU PR PRGPU PRN PRGPUN`,
then `node /work/src/run.mjs /bin-cft/157.0.8103.38/chrome-linux64/chrome C157S /work/pages /assets /out 2 PX PXGPU PR PRGPU PRN PRGPUN`.
`python3 score.py results/pixijs-8.23.0 > results/pixijs-8.23.0/score.json` prints its table from our
records and regenerates our `score.json` byte for byte; the `C157S` cells are in `score.json`.
After the run we changed only comments and descriptions: the source and license notices at the
top of the adapted pages, the first line of `probe.js`, `run.mjs`, `run_all.sh` and `score.py`,
and the census list's file name and `note` text.
