# ECMWF open data now stores rain in steps coarser than 0.1 mm from 24 hours ahead. A 0.1 mm chance of rain moved by 10 points or more at a fifth of uncertain land points (October 29)

Since its 20 October 2026 06 UTC run, ECMWF's free and open forecast data stores total precipitation (`tp`) with 12
bits per value instead of 16. ECMWF's page
[ECMWF open data: bits per value](https://confluence.ecmwf.int/spaces/DAC/pages/738041093/ECMWF+open+data+bits+per+value)
(version of 20 October) says the removed bits do not matter: "the values people read, and the fields they compute with,
are unchanged to well within their own accuracy", and "The rounding is uniform and bounded at each grid point, with no
bias or artefacts."

We tested that for one product that weather apps commonly compute from these files: the chance of more than 0.1 mm of
rain in a 6-hour window, as the share of the 50 ensemble members above that amount. The same change cut snow depth
to 9 bits, and there shallow snow now reads zero ([below](#snow-depth-shallow-snow-now-reads-zero)).

**The step is now coarser than 0.1 mm.** We read the packing header of `tp` in the 28 October 00 UTC HRES run: the
step is 0.061 mm at 6 h, 0.122 mm at 24 h and 0.244 mm from 48 h to 360 h. In the 15 October run, before the change, it
was 0.008 to 0.031 mm.
The step follows each field's largest value, so it can differ from day to day.

**What moves.** We took two runs published before the change, 15 and 19 October (00 UTC, 0.25°), and re-encoded their
`tp` at 12 bits with ecCodes 2.50, letting it choose the scale. The re-encoded steps were 0.061 to 0.488 mm, mostly 0.122 or
0.244 mm, depending on the run, member and forecast step. We then computed 6-hour amounts as differences of the accumulations, on land points only,
and compared the products from the original and re-encoded files of the same weather.

| | 15 Oct run | 19 Oct run |
|---|---|---|
| Ensemble chance of > 0.1 mm in 6 h: uncertain land point-windows that move by 10 points or more | 19.6 % | 20.7 % |
| … that move by 20 points or more | 5.5 % | 5.8 % |
| … 10 points or more, as a share of all land point-windows | 13.6 % | 14.4 % |
| The same at > 1 mm instead of > 0.1 mm (10 points or more, uncertain) | 0.98 % | 0.84 % |
| HRES 6 h rain or no rain at 0.1 mm: windows that flip, per originally wet window | 25.0 % | 25.4 % |
| HRES 24 h, the same | 14.5 % | 17.3 % |

A point-window is one land grid point in one 6-hour window, up to 144 h for the ensemble. Uncertain means some but not
all members had more than 0.1 mm, before or after re-encoding; at other points the chance is 0 % or 100 % and stays so.

**It moves up more often than down.** On the uncertain point-windows the average change is +4.2 points, with a 95 %
bootstrap interval of +3.3 to +5.3 points over the 48 windows of both runs. Neighbouring windows are correlated, so the
true interval is wider. Each field's rounding may well be unbiased, as ECMWF says. A 0.1 mm threshold applied to the
difference of two rounded accumulations is not, once the step is larger than the threshold.

**Why.** About 36 % of ensemble member-windows with more than 0.1 mm (36.8 % and 35.5 %) hold less than one 12-bit
step of rain. At 1 mm, above the step, the effect falls to about 1 %.

**What we did not find.** We expected more negative 6-hour amounts, where a later accumulation rounds below an earlier
one. The re-encoded runs have slightly fewer (0.58 % to 0.52 % and 0.90 % to 0.73 % of ensemble member-windows), so we
do not claim that.

## Snow depth: shallow snow now reads zero

Snow depth (`sd`, metres of water equivalent) went from 16 bits to 9. We read its packing header in the 15 and 28
October 00 UTC HRES runs at 0, 24, 144 and 240 h: the step was 0.24 mm and is now 31.25 mm of water equivalent, with
a reference value of 0. So every stored value is a multiple of 31.25 mm. The 28 October file at 24 h holds no value
between 0 and 31.25 mm.

We wrote a plan for this check before downloading any snow data ([`sd/PRE-SD.md`](reproduce/sd/PRE-SD.md)). We
rounded the real 16-bit `sd` of the 15 and 19 October runs (00 UTC, 24 h) to the new 31.25 mm step, so the snow is the
same in both versions, and counted land points with at least 1 mm of water equivalent.

| | 15 Oct run | 19 Oct run |
|---|---|---|
| Snow-covered land points that read 0 after rounding to the nearest step (planned measure) | 19.5 % | 18.3 % |
| … re-encoded at 9 bits with ecCodes 2.50 instead | 19.4 % | 18.1 % |
| … rounding down instead (upper bound) | 25.3 % | 25.5 % |

Those percentages include ice sheets and glaciers. About two thirds of the snow-covered points (68 % and 66 %) hold
9.9 m of water equivalent or more. We chose the next split after seeing the results, so treat it as exploratory.
Without those points, 60.1 % and 53.8 % of seasonal-snow land points read 0 (71.5 % and 64.7 % between 30° N and
70° N). Snow depth in centimetres, computed as `sd` divided by snow density (`rsn`), changes by 5 cm or more at 28.7 %
and 32.0 % of them.

Our first script left out a factor of 1,000 when converting to centimetres. We fixed it after the results
([`sd/AMENDMENT-SD-01.md`](reproduce/sd/AMENDMENT-SD-01.md)). The zero counts above do not use that conversion, and
the first output is kept unedited.

Limits: two dates early in the season, when snow is shallow, so the share will be lower in mid-winter. HRES only, one
forecast step, no ensemble. Snow density was taken from the original files in both versions.

## If you compute rain chances from these files

Check the step in the files you use with the one-line command in [`reproduce/`](reproduce/README.md#check-the-step-in-a-file-you-use).
If your rain or no-rain threshold is below it, products built on that threshold changed on 20 October. A 1 mm
threshold moved about 1 % in our test. Products with shorter windows, such as hourly amounts, use the same files; we did
not test hourly windows or any service's own processing. We have not tested a fix.

If you show snow depth or snow cover from `sd`, read the step with the same command (`sd` instead of `tp`). Snow
under about half a step, 15.6 mm of water equivalent, now reads 0.

## Limits

- Two October runs, 00 UTC, 0.25° only, 6-hour and 24-hour windows. The 0.1° data introduced on the same day was not
  tested.
- The original files were already rounded to 16 bits, not full precision. Our main arm re-encodes them; a second arm
  that adds sub-step noise first, as an upper bound, agrees within about 1 point (19.7 % and 21.3 %).
- We did not score forecasts against observations, so "within their own accuracy" in the sense of forecast skill is
  not tested. The 10-point bar is our judgement of a change a reader would see, since apps often show the chance in
  tens.
- We wrote the plan and froze it before the main run. Its code stopped with an instrument error: one check required 12
  bits on every re-encoded message, including the 102 all-zero messages at step 0, which ecCodes stores with 0 bits.
  The plan's text exempts all-zero messages, and 0 of the 2,520 other messages failed. Under the plan's text the
  verdict is that the claim is contradicted for these products. We recorded this correction after seeing the results
  ([`AMENDMENT-02.md`](reproduce/AMENDMENT-02.md)). The numbers above are the same either way.

## Reproduce

[`reproduce/`](reproduce/) holds the frozen plan, both amendments, the scripts, the image recipe, the output
(`out/result.json`) and the sha256 of every input file. The inputs are public and the fetch script downloads them again.
See [`reproduce/README.md`](reproduce/README.md).

On 29 October we reran both parts from the commands in `reproduce/README.md`, in fresh folders. All re-downloaded
input files matched the sha256 lists, and the image was rebuilt without cache. `result.json`, `sim12-census.json` and
both snow outputs came out byte for byte identical. Nobody outside the company has reproduced it.

These results are based on data and products of the European Centre for Medium-Range Weather Forecasts (ECMWF).
Copyright "© 2026 European Centre for Medium-Range Weather Forecasts (ECMWF)". Source www.ecmwf.int. This data is
published under a Creative Commons Attribution 4.0 International licence (CC BY 4.0),
https://creativecommons.org/licenses/by/4.0/. ECMWF does not accept any liability whatsoever for any error or omission
in the data, their availability, or for any loss or damage arising from their use. Modified: we re-encoded the
precipitation field at 12 bits and computed 6-hour and 24-hour amounts and threshold products from it, and rounded the
snow depth field to the 9-bit step, as described above.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai. We will publish
dated corrections here.
