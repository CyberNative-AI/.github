# Chrome 155 now gets JPEG XL from some Cloudinary sites

Snapshot: October 12, 2026.

Chrome 155 added `image/jxl` to the Accept header it sends for images. Cloudinary's `f_auto` reads that header. On sites whose Cloudinary setup includes JPEG XL, Chrome 155 now gets JPEG XL where Chrome 154 got AVIF or WebP. In Tranco's top 50,000 homepages that was 28 of the 237 sites using `f_auto`, about 1 in 8. A real Chrome 155 browser got the same files as our scripted requests.

What it does to bytes depends on the image. In a sample of image URLs taken from homepage HTML, the JPEG XL file was usually larger (median 1.40x) and scored higher on a perceptual quality metric. On four homepages we loaded in Chrome, the difference was small and went both ways (median 1.07x). If you serve images through `f_auto`, check what your own URLs now return.

## Check one of your own URLs

[jxlcheck.py](jxlcheck.py) uses only the Python standard library. It starts two requests for each supplied URL, once with Chrome 154 desktop request headers and once with Chrome 155's, and identifies the format from the file's first bytes. Use it locally on your own or trusted HTTP(S) image URLs. It follows redirects, uses Python's system proxy settings and reads each complete response into memory. Its 30-second socket timeout is not a total runtime limit, and response size is not capped. It writes no files and runs no shell commands; it is not a service for accepting untrusted URLs.

```sh
python3 jxlcheck.py 'https://res.cloudinary.com/demo/image/upload/w_500,f_auto/v1612277603/docs/shoes.jpg'
```

```text
chrome154	chrome155	ratio	url
avif 13,076 B	jxl 21,557 B	1.65x	https://res.cloudinary.com/demo/image/upload/w_500,f_auto/v1612277603/docs/shoes.jpg
```

That is the example image from [Cloudinary's image optimization docs](https://cloudinary.com/documentation/image_optimization), whose table lists AVIF at 14.6 KB and JPEG XL at 21.4 KB. Not every image grows. Two other docs-example URLs gave 1.19x (`c_scale,w_500/q_auto/f_auto/docs/camera.jpg`) and 0.94x (`q_auto/f_auto/docs/shoes.jpg`) on the same day.

## What changed in Chrome

Headers captured from Chrome for Testing builds for an `<img>` request:

```text
Chrome 154.0.8037.92   image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8
Chrome 155.0.8059.39   image/jxl,image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8
```

[Chrome's announcement](https://developer.chrome.com/blog/jpeg-xl-in-chrome) (October 6) says "In general, we recommend trying both AVIF and JPEG XL to get the best results." A format-negotiating CDN makes that choice for you. We sent both headers to sample URLs on seven other image services, either in their automatic-format mode or as configured on a public site: imgix, ImageKit, Fastly Image Optimizer, Akamai Image Manager, Shopify, Sirv and TwicPics. None changed its answer for Chrome 155. That was one or two URLs per service on one day, so it doesn't show that they never will.

## How common it is

We took homepages ranked 1 to 50,000 on [Tranco list 4672X](https://tranco-list.eu/list/4672X) and read their static HTML. 237 of them reference Cloudinary-style `f_auto` image URLs. We fetched up to six of those URLs per site with both headers. 28 sites served JPEG XL to Chrome 155. Cloudinary's docs say that on image-impressions plans "AVIF and JPEG XL formats are automatically supported as possible `f_auto` formats", and that on bandwidth plans they aren't by default. The 1-in-8 share fits that, but we can't see any site's plan.

Checks on the switch: a request with Chrome 154's User-Agent and Chrome 155's Accept header got the same format as Chrome 155 for 144 of 144 images, so the Accept header drives it. A Firefox-style header without `image/jxl` never received JPEG XL. A second pass over 24 sites returned identical bytes for 240 of 242 responses.

## In a real browser

Scripted requests can miss what a browser adds, such as client hints. So we loaded nine of the 28 homepages in headless Chrome 154 and 155 (desktop, 1366x768, cache off) and logged every image response. Chrome sent only the `sec-ch-ua` hints. We then requested every `f_auto` URL the browser loaded with our scripted headers: all 58 Chrome 155 files and all 53 Chrome 154 files were byte-for-byte identical to what the browser received.

Four of those pages gave a usable Chrome 154 vs 155 comparison. On the 51 switched images they actually loaded, the JPEG XL was 1.07x the Chrome 154 file at the median and 1.02x in total bytes; 22 were at least 10% larger and 18 were at least 10% smaller. On two of the four sites the direction differed from what the URL sample below showed. Four other homepages loaded no `f_auto` image at all once rendered. Four sites is too few to estimate anything with, but it shows the larger-file result below belongs to the URLs we sampled, not to pages as people load them.

## The URL sample: larger, and higher measured quality

On the 28 sites, from the static-HTML URL sample:

| | |
|---|---|
| Images where Chrome 155 got JPEG XL | 144 |
| Median size, Chrome 155 ÷ Chrome 154 | 1.40x |
| Total bytes, same 144 images | 1.32x |
| Images at least 10% larger | 107 of 144 |
| Estimated distinct images, per-site URL grouping | 86 |
| Sites whose median grouped image is at least 10% larger | 20 of 28 |
| Where Chrome 154 had received AVIF (130 images) | median 1.43x |
| Where Chrome 154 had received WebP (14 images) | median 0.97x |

Many of the 144 URLs are `srcset` widths of one image; on one site all six were. Our per-site grouping removes leading transformation and version segments and the file extension from an image's asset path. This is a heuristic: it can merge different crops or effects. Other grouping rules gave 88 or 91 groups instead of 86; all gave 20 of 28 sites with a median grouped-image ratio of at least 1.10x.

For 16 distinct images, all from a handful of site owners, we could also fetch the untransformed original. We scored both delivered versions against it with SSIMULACRA2 (the Python port, version 0.3.0). The median JPEG XL scored 5.4 points higher than the file Chrome 154 received; 2 of the 16 scored lower. That looks like a different quality target per format, rather than JPEG XL compressing worse. We can't see how `f_auto` decides, and this note doesn't compare the two formats' compression efficiency. The Python quality-metric port ignores ICC profiles; images with alpha were excluded, and the internal rerun did not recompute quality scores.

## If you use `f_auto`

- Run `jxlcheck.py` on a few of your own `f_auto` URLs, and measure the pages you care about in Chrome 155 rather than relying on our sample.
- If you'd rather not serve JPEG XL, Cloudinary's docs say: "You can limit the number of potential delivery formats by contacting support."
- Or name the format in the URL instead of using `f_auto`, and keep a fallback for browsers without it.

## What this does not show

We measured bytes only: no Largest Contentful Paint, decode time, difference people notice or business effect. We used desktop Windows Chrome only, with no mobile, Save-Data or high-DPR variants. The URL sample comes from static homepage HTML, so it misses images inserted by JavaScript; on one rendered page, images whose URLs didn't contain `f_auto` also switched, so URL matching undercounts. All requests came from one network location in the western US. Tranco's top 50,000 is not Cloudinary's customer base. Cloudinary can change `f_auto` at any time; every number here is from October 12, 2026.

A separate rerun inside our company repeated the analysis, refetched a sample of 53 images with a separately written client and ran the browser check above; it got the same bytes. It used the same network location, and nobody outside our company has reproduced this yet.

We don't list the sites. Chrome 154 and Chrome 155 headers requested the same URLs seconds apart, so the switch came from the browser's header, not from anything the sites changed.

## Data and method

- [images.csv](images.csv): the 144 URL-sample images, with sites shown as S01 to S28, delivery hosts as C01 to C25 and per-site asset groups as A001 to A086.
- [rendered.csv](rendered.csv): the 51 switched images from the four rendered homepages, using the same site codes.
- [quality.csv](quality.csv): the quality rows, including duplicates where two sites share images, and rows excluded because the image has an alpha channel.
- [summary.json](summary.json): frame counts, controls and breakdowns by size.
- `python3 recompute.py` recomputes the URL-sample, rendered-image and quality statistics from the three CSV files. `summary.json` records the original frame counts and controls; the CSVs do not independently verify frame discovery or live requests.

We froze the main-frame analysis rules before requesting main-frame image responses. Earlier pilot and CDN-example measurements informed the protocol. The first frame, ranks 1 to 20,000, gave only 12 JPEG XL sites, below the minimum of 20 we had set, so it doesn't count as a result. We extended the frame to 50,000 with the same code and thresholds and decided once, on the combined frame. The browser check and the distinct-image count were added after that decision.

Published by CyberNative AI LLC. AI systems prepared the note, performed the measurements and analysis, and carried out the internal rerun; measurement limits are stated above. Corrections: hello@cybernative.ai. Material corrections will be published with dates.
