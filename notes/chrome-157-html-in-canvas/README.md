# Chrome 157 drops the HTML-in-Canvas names that three.js, PlayCanvas, Babylon.js and PixiJS call: their HTML textures went blank in our test, and 157 is already rolling out (October 23)

In Chrome 157, HTML-in-Canvas worked in our test with no flag and no origin-trial token. The
same build no longer has `texElementImage2D`, `copyElementImageToTexture` or the `layoutsubtree` canvas
attribute, and those are the names the current releases of three.js (0.186.x), PlayCanvas
(2.23.3), Babylon.js (9.32.0) and PixiJS (8.22.0) call. On Chrome 157.0.8103.15, a minimal
HTML texture built with each of the four rendered nothing. Three of them logged nothing either.
All four rendered on Chrome 156 with the feature turned on, which is what origin-trial sites
run today.

Babylon.js broke beyond trial sites in our test. With its defaults, Babylon.js 9.32.0's
`HtmlTexture` drew on plain Chrome 156 through its SVG fallback, with no flag or trial. On 157
the same minimal page was blank. So a default Babylon HTML texture can stop drawing for ordinary
Chrome visitors, not only on trial sites. We tested one minimal WebGL scene, not real apps.

Chrome 157 is already reaching people. On October 22 Google moved the Windows Stable channel to
157.0.8103.15/.16 "as part of our early stable release to a small percentage of users", and on
October 23 released 157.0.8103.14 for Android "to a small percentage of users". The full Stable
release is scheduled for November 3.

**If your page puts HTML into a canvas, open it in Chrome 157 now.** Your own code needs the new
names: `content="drawable"` on the canvas, `texElementSubImage2D` into a texture you allocated
first (WebGL), `drawElementImageToTexture` (WebGPU), each called from the canvas's `onpaint`; the
code below rendered on 157 and 158. For three.js, PlayCanvas and PixiJS the fix has to come from
the engine, or from your own patch to it. A three.js pull request that is not merged yet rendered
on 157. On October 23 we found no fix, issue or pull request for PlayCanvas, Babylon.js or PixiJS
that mentions the new names. For Babylon.js 9.32.0 there is a workaround in your own code:
calling the texture's `update()` yourself brought it back on 157 in our test (below).

## Update, 29 October 2026

**Babylon.js 9.33.0 fixes this. If you use `HtmlTexture`, upgrade.** Babylon.js 9.33.0, published
on npm on October 29, includes the fix from Babylon.js pull request
[#19052](https://github.com/BabylonJS/Babylon.js/pull/19052), opened after our report on the
Babylon.js forum. We reran our minimal Babylon page with 9.33.0 instead of 9.32.0, nothing else
changed, on the same four browsers, two loads each. With defaults, the texture rendered on Chrome
157.0.8103.15 and 158 Canary, where 9.32.0 was blank. There Babylon reported native upload
support and set `content="drawable"` on the canvas itself. It still rendered on 156, with and
without the feature.

The `update()` workaround below also still rendered on 9.33.0. But with the feature available
(157, 158, and 156 with it turned on), the early call now logs "HTML-in-Canvas: the native upload
failed" once, so remove the call when you upgrade.

The other engines, as of October 29:

- **PlayCanvas** merged its fix ([#9824](https://github.com/playcanvas/engine/pull/9824)) on
  October 26. It is in the 2.24.0 beta builds, not in a stable release. The latest release is
  still 2.23.3.
- **PixiJS** has a draft fix, [#12341](https://github.com/pixijs/pixijs/pull/12341), which is not
  merged. Its preview build rendered on 157 and 158 on our page
  ([our result](https://github.com/pixijs/pixijs/issues/12340#issuecomment-6462080964)). The
  latest release is still 8.22.0.
- **three.js** pull request [#34732](https://github.com/mrdoob/three.js/pull/34732) is still open.
  The latest release is still 0.186.1.

The 9.33.0 pages, records, screenshots and scores are in
[`reproduce/results/babylon-9.33.0/`](reproduce/results/babylon-9.33.0/). The rest of this note
is as published on October 23.

## Why now

On October 22 Chrome's May post
[Introducing the HTML-in-Canvas API origin trial](https://developer.chrome.com/blog/html-in-canvas-origin-trial)
was posted to [Hacker News](https://news.ycombinator.com/item?id=50200164), where it had 112
points on October 23. The post, last updated May 19, still teaches `layoutsubtree`,
`texElementImage2D` and `copyElementImageToTexture`, and names three.js and PlayCanvas as
libraries with support.

Chrome's September 29 post
[HTML-in-Canvas updates: Iterating toward a better Web API](https://developer.chrome.com/blog/html-in-canvas-ot-changes)
renamed all three in Chrome 155 and extended the origin trial through Chrome 160. Its sample
code still falls back to the old names. Neither post says the old names stop working in 157. In
our runs, Chrome 156 with the feature on had both the old and the new names; 157 and 158 had only
the new ones.

## What we measured

Each cell is two fresh loads of a test page in headless Chrome for Testing on Linux; the two
loads agreed in every cell. "Blank, silent" means no HTML texture on screen and no exception or
console error. "Blank, error" means no texture and an exception or console error.

| Page | Chrome 156 | Chrome 156, feature on | Chrome 157 | Chrome 158 |
|---|---|---|---|---|
| three.js 0.186.0 `HTMLTexture` | blank, silent | renders | **blank, silent** | blank, silent |
| three.js pull request 34732 | blank, silent | renders | **renders** | renders |
| PlayCanvas 2.23.3 HTML texture | blank, error (our page) | renders | **blank, silent** | blank, silent |
| Babylon.js 9.32.0 `HtmlTexture`, defaults | renders (SVG fallback) | renders | **blank, silent** | blank, silent |
| Babylon.js 9.32.0, fallback off | blank, warning | renders | **blank, silent** | blank, silent |
| PixiJS 8.22.0 `HTMLSource` | blank, error | renders | **blank, error** | blank, error |
| New names, 2D / WebGL / WebGPU | blank, error | renders | renders | renders |
| Chrome blog 2D snippet, adapted | blank, error | renders | blank, error | blank, error |
| Chrome blog WebGL snippet, adapted | blank, error | blank, error | blank, silent | blank, silent |
| Chrome blog WebGPU snippet, adapted | blank, error | blank, error | blank, error | blank, error |

Chrome 156 is 156.0.8078.47, "feature on" adds `--enable-blink-features=CanvasDrawElement` (our
stand-in for an origin-trial token), 157 is 157.0.8103.15 and 158 is Canary 158.0.8119.0. On plain
156 our PlayCanvas page throws `canvas.requestPaint is not a function` itself, because it follows
the PlayCanvas pattern in Chrome's blog; PlayCanvas does not throw. Every page in the bottom
three rows, and our new-name pages on 156, throw at that same `requestPaint` call on plain 156.
Positive and negative control pages gave the expected result in all four browsers.

## What each engine does on Chrome 157

- **three.js 0.186.x:** blank, nothing in the console. It looks for `texElementImage2D`, does not
  find it, and never moves the element into the canvas; our probe saw no `paint` event. npm's
  current 0.186.1 ships the same `build/three.module.js` byte for byte (sha256 `9052042d…`), so
  this holds for its WebGL renderer. We did not run its WebGPU renderer.
- **three.js
  [pull request 34732](https://github.com/mrdoob/three.js/pull/34732)**, "HTMLTexture: Support the
  Chromium 155+ HTML-in-Canvas API changes" (head `b28067fa`): renders on 157 and 158. It was
  open with no review on October 23.
- **PlayCanvas 2.23.3:** blank, nothing in the console. `device.supportsHtmlTextures` is `false`
  on 157, so the texture is never filled. PlayCanvas's main branch on October 23
  (`4c8301b4`, 2.24.0-beta.20) still calls only `texElementImage2D` and
  `copyElementImageToTexture` in its WebGL and WebGPU texture code.
- **Babylon.js 9.32.0:** blank, nothing in the console, with or without the SVG fallback. We did
  not instrument why. Reading `htmlTexture.js`, our best explanation is that 157 has
  `canvas.requestPaint`, so the texture waits for a `paint` event instead of updating, and the
  update never reaches the upload; Babylon also sets `canvas.layoutSubtree`, which on 157 no longer adds the `layoutsubtree`
  attribute, and never sets `content="drawable"`.
  That is an inference, not a measurement.
- **PixiJS 8.22.0:** blank, and it throws `Error: [HTMLSource] WebGLRenderingContext.texElementImage2D is not available. Enable the browser HTML-in-Canvas API before using HTMLSource.`
  On 157 the API is already on, so the advice sends you the wrong way. PixiJS's `dev` branch on
  October 23 (`b78ff351`) still calls only the old names and sets `layoutsubtree`.

## Babylon.js 9.32.0: call `update()` yourself

`HtmlTexture.update()` uses the SVG fallback when the native upload is missing, which it is on
157. Calling it directly, instead of waiting for the `paint` event, brought the texture back on 157 and 158:

```js
const tex = new BABYLON.HtmlTexture('h', el, { scene, width: 200, height: 100 });
mat.emissiveTexture = tex;
tex.update();
// after you change the element:
tex.update();
```

| Page | Chrome 156 | Chrome 156, feature on | Chrome 157 | Chrome 158 |
|---|---|---|---|---|
| Babylon.js 9.32.0 defaults (repeated) | renders | renders | blank, silent | blank, silent |
| defaults + `tex.update()` | renders | renders | **renders** | renders |
| element changed from green to magenta after 1.5 s, then `tex.update()` again | magenta | magenta | **magenta** | magenta |

On 156 with the feature on, the early `update()` call logs "HTML-in-Canvas: the native upload
failed" (Babylon's source says the native call fails before the first paint snapshot); the
texture still renders there. We added these pages after the main run, ran them in a separate run of the same
harness, and repeated the defaults page and the controls in it. Our first attempt at that run lost
its plain-156 loads to a file-permission error in our setup, so the runner found no page to
record. We discarded that attempt, fixed the permissions and reran all four browsers; the table
above comes from the rerun alone.

We tested this on Babylon.js 9.32.0 only, on the same minimal page. On 157 the texture is an
SVG `foreignObject` snapshot of the element, not the native HTML-in-Canvas texture. In the
second page we changed the element after 1.5 seconds and called `update()` again, and the
texture showed the new colour; we did not test a change without that second call. The same two
textures, one with defaults and one with `update()`, are in
[Babylon Playground #YT6MOH](https://playground.babylonjs.com/#YT6MOH): in our check it ran
Babylon.js 9.32.0, both rendered on 156, and only the `update()` one rendered on 157 and 158.

## What rendered on Chrome 157

Shortened from our new-name pages, which rendered on 157 and 158 (and on 156 with the feature
on). The
canvas needs `content="drawable"`; our element also carries `drawable`, as in Chrome's
September 29 post.

```html
<canvas id="c" width="400" height="300" content="drawable">
  <div id="el" drawable style="width:200px;height:100px">HIC</div>
</canvas>
```

WebGL 2 (`texElementSubImage2D` no longer allocates the texture, so allocate it once first):

```js
const gl = c.getContext('webgl2');
const tex = gl.createTexture(); // plus your usual texture parameters
let alloc = false;
c.onpaint = () => {
  gl.bindTexture(gl.TEXTURE_2D, tex);
  if (!alloc) { gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, 200, 100, 0, gl.RGBA, gl.UNSIGNED_BYTE, null); alloc = true; }
  gl.texElementSubImage2D(gl.TEXTURE_2D, 0, 0, 0, el);
  // draw with tex
};
c.requestPaint();
```

WebGPU (`ctx` is the canvas's `webgpu` context, configured with usage
`RENDER_ATTACHMENT | COPY_DST`):

```js
c.onpaint = () => {
  device.queue.drawElementImageToTexture({ source: el }, { texture: ctx.getCurrentTexture(), size: { width: 200, height: 100 } });
};
c.requestPaint();
```

In 2D, `ctx.drawElementImage(el, 0, 0)` drew on 157, but returned nothing. Our 2D page, which
still set `el.style.transform` from the return value as Chrome's May post shows, drew the
element and then threw `TypeError: Cannot read properties of undefined (reading 'toString')`.
Chrome's September 29 post says 155 and later keep the element's position in sync on their own,
so that line can go.

## Chrome's own snippets

Our pages built from the three rendering snippets in the May post did not work on 157. We kept
each snippet's code and added the element's size and colour, a `requestPaint()` call, our test
probe and, where a snippet leaves it out, the context setup and a draw:

- 2D: `InvalidStateError: Failed to execute 'drawElementImage' on 'CanvasRenderingContext2D': DrawElementImage requires the canvas to have the content=drawable attribute`
  (the snippet uses `layoutsubtree`).
- WebGL: blank with no error, because the snippet checks `if (gl.texElementImage2D)` first. On
  156 with the feature on it already threw a `TypeError`, since its six-argument form predates
  Chrome 150's change.
- WebGPU: `copyElementImageToTexture is not a function` on 157. On 156 with the feature on it
  already threw, since it passes the element instead of a `{ source }` dictionary.

## Who else still references only the old names

A GitHub code search on October 23 found 143 public repositories, from 132 owners, whose matched
code files reference `texElementImage2D` or `copyElementImageToTexture` and none of the new
names. We left out forks; the engine and specification repositories (three.js, PlayCanvas,
Babylon.js, PixiJS and WICG/html-in-canvas); files whose path marks them as a copy of an engine,
a vendored library or three.js's renderer source; and repositories with any matched file that
also uses a new name. 77 of the 143 had a push since September 23. This reads the text of the
files the search returned; it does not parse calls or read the rest of each repository.
Re-read at their default branch on October 23, every hit file still references only the old
names in
[heygen-com/hyperframes](https://github.com/heygen-com/hyperframes),
[shader-effects-inc/shaders](https://github.com/shader-effects-inc/shaders),
[AndrewPrifer/liquid-dom](https://github.com/AndrewPrifer/liquid-dom),
[visgl/luma.gl](https://github.com/visgl/luma.gl), [openfilm/openfilm](https://github.com/openfilm/openfilm)
and Remotion's demo [remotion-dev/html-in-canvas](https://github.com/remotion-dev/html-in-canvas).

Copied agent skills lag too. Google's
[modern-web-guidance](https://github.com/GoogleChrome/modern-web-guidance) HTML-in-Canvas guides
were updated on October 15 and released on October 19. Of 261 repositories holding a copy, 252
still teach only the old names at their default branch. Of 255 repositories with a copy of
Remotion's `html-in-canvas` skill in GitHub's code index, 198 do not mention the new names;
Remotion's own skill was updated on September 30. If you copied either into a skills folder,
copy it again.

## How we tested

Each page loaded in a fresh profile of headless Chrome for Testing in a Linux container with no
network, rendering through SwiftShader on the CPU. We screenshotted the canvas at 4 and 7
seconds and counted magenta pixels from the 200 × 100 magenta element: at least 4,000 is
"renders", under 400 is "blank". A probe recorded which API names exist, the `paint` events, and
each engine's own feature checks. Engine code came from the npm tarballs, the pull request from
its head commit; every input's sha256 is in `reproduce/assets.json`. We wrote down the pages,
the scoring rule and our forecast before the main run.

The census searched GitHub code for the two removed method names in JavaScript, TypeScript,
HTML, Vue, Svelte and Markdown files, fetched each hit and checked its text for the new names.
Skill copies were found by file name.

Our test pages adapt code samples from Chrome's May and September posts, which Google licenses
under the Apache License 2.0; `reproduce/LICENSE-Apache-2.0.txt` has the license, and each
adapted page names its source and our changes. The WebGL and WebGPU code above is shortened from
those pages.

[`reproduce/`](reproduce/) has every page, the runner, the scorer, each load's raw record, every
screenshot and the scores; `python3 score.py results/main` there recomputes the main table.

## Limits

- One machine, headless Linux, SwiftShader. A real GPU, another operating system or Android may
  differ, most of all for WebGPU.
- We tested 157.0.8103.15, the build now on Windows early Stable. A later 157 build could change
  this; we will rerun on November 3.
- "Feature on" is a command-line flag, not an origin-trial token.
- Minimal scenes, not the engines' own examples. An app that sets `content="drawable"` itself may
  get further than our pages.
- 143 counts public repositories in GitHub's code index, from the text of their matched files,
  including demos and tests. It is not a count of calls that run, or of websites.
- The Babylon.js explanation is read from its source, not measured.
- We ran all of this ourselves, on October 23. Nobody has reproduced it independently.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai. We will publish dated corrections here.
