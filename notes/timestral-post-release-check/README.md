# Timestral on data it can't have trained on: a tie with Chronos-2 on US grid demand, about 3–10% ahead on Wikipedia pageviews

*CyberNative AI LLC, 24 October 2026. Run once on our own machine on 24 October; nobody else has reproduced it yet.*

Mistral released the Timestral time-series models on 15 October 2026 without publishing a training cutoff, and
people asked how to score them without leakage. One bound needs no answer from Mistral: data
that didn't exist when the weights were published can't be in their training set. The Timestral-209M repository
was created on the Hugging Face Hub on 14 October 08:52 UTC and its first listed commit is 15 October 15:22 UTC, so
we scored every model only on targets dated 16 October or later.

## What we ran

- **US grid demand.** EIA-930 hourly demand (`Demand (MW) (Adjusted)`), 50 balancing authorities, a forecast
  issued at 00:00 UTC each day from 16 to 22 October, 24 hours ahead: 350 forecasts per model.
- **English Wikipedia daily pageviews.** 150 of August 2026's most-viewed articles (user traffic), forecasts issued
  16 and 17 October, 7 days ahead: 300 forecasts per model.
- **Models.** Timestral 5M, 28M and 209M; Chronos-2 and Chronos-2-small; TimesFM-2.5; and from statsforecast
  seasonal naive, AutoETS, MSTL (grid only) and AutoARIMA (pageviews only). Pinned model revisions are in
  [`reproduce/src/install.sh`](reproduce/src/install.sh).
- **Settings.** Zero-shot, one series at a time, no weather or calendar inputs, library defaults, CPU (6 threads),
  no network. Every model got the same context: the last 2,048 hours or 512 days.
- **Score.** MASE of the median forecast, scaled by the seasonal-naive error inside the context. A ratio A/B is
  the geometric mean over series of per-series MASE ratios; below 1 means A was better. Brackets are 95%
  bootstrap intervals over series. The [protocol](reproduce/PROTOCOL.md) was written before any October or
  September forecast was produced.

## Results

Timestral-209M against each model, October targets:

| Timestral-209M vs | Grid demand (50 series) | Wikipedia pageviews (150 series) |
|---|---|---|
| Chronos-2 | **1.007** [0.976, 1.038], a tie | **0.897** [0.844, 0.955] |
| TimesFM-2.5 | 0.874 [0.846, 0.902] | 0.927 [0.883, 0.971] |
| MSTL | 0.632 [0.575, 0.697] | not run |
| AutoETS | 0.352 [0.304, 0.408] | 0.414 [0.348, 0.485] |
| AutoARIMA | not run (too slow on hourly data) | 0.388 [0.319, 0.461] |
| Seasonal naive | 0.695 [0.651, 0.742] | 0.631 [0.567, 0.700] |

Every model against seasonal naive (geometric mean of per-series MASE ratios; lower is better) and CPU time for
all forecasts:

| Model | Grid | Grid CPU s (350) | Pageviews | Pageviews CPU s (300) |
|---|---|---|---|---|
| Chronos-2 | 0.691 | 63 | 0.703 | 16 |
| Timestral-209M | 0.695 | 112 | 0.631 | 23 |
| Timestral-28M | 0.723 | 18 | 0.678 | 5 |
| Timestral-5M | 0.737 | 9 | 0.691 | 2 |
| Chronos-2-small | 0.758 | 28 | 0.761 | 8 |
| TimesFM-2.5 | 0.796 | 127 | 0.681 | 31 |
| Grid operators' own day-ahead forecast (reference only) | 0.845 | | | |
| Seasonal naive | 1.000 | 3 | 1.000 | 2 |
| MSTL | 1.100 | 46 | | |
| AutoETS | 1.976 | 129 | 1.524 | 26 |
| AutoARIMA | | | 1.629 | 174 |

What we take from it:

- **Grid demand: no lead.** Timestral-209M and Chronos-2 tie, and Chronos-2 took 63 s against 112 s for the same
  350 forecasts on our CPU.
- **Pageviews: Timestral-209M is ahead, by about 3–10% depending on the average.** It is 10% better than Chronos-2
  and 7% better than TimesFM-2.5 on the geometric mean above; on the plain mean of MASE the gaps are 2.5% (0.5444
  vs 0.5581) and 3.1% (0.5444 vs 0.5619), because a few hard, news-driven pages dominate that average.
- **Every foundation model beat seasonal naive by at least 20% on both datasets.** On the geometric mean, AutoETS
  and AutoARIMA were worse than seasonal naive here; on the plain mean of MASE, AutoARIMA on pageviews was slightly
  better than seasonal naive (0.900 vs 0.929). So "it didn't beat AutoARIMA" depends on the data and the average.
- **The small Timestral models are not as good as 209M here:** 5M is 6% behind on grid demand (1.060 [1.034,
  1.086]) and 9% behind on pageviews (1.094 [1.056, 1.136]), but it beat every classical model and ran 12x faster
  on grid demand. Timestral-28M beat Chronos-2-small on both (0.954 [0.924, 0.984] and 0.891 [0.833, 0.951]).
- **The grid operators' own forecasts are not a fair comparison:** they are issued at a different time and use
  weather. Timestral-209M against them: 0.823 [0.660, 1.015], a tie.

## Leakage probe

We ran the same comparison on a September window (forecasts issued 16–22 September for grid demand, 16–17
September for pageviews), which could be in Timestral's training data. The pattern is the same: Timestral-209M /
Chronos-2 is 0.991 [0.968, 1.016] on grid demand and 0.926 [0.865, 0.995] on pageviews. The difference in
differences (September ratio over October ratio) is 0.985 [0.950, 1.024] on grid demand and 1.032 [0.946, 1.128]
on pageviews. A value well below 1 would have meant a larger advantage on the window Timestral could have seen;
neither is. September and October also differ in season and weather, so this is a probe, not proof either way. It
says nothing about the GIFT-Eval, TIME or fev-bench test windows.

## Checks

- **Time alignment:** the grid operators' forecast error against actuals is lowest with no shift (0.042) and
  rises at ±1 hour (0.054, 0.055) and ±2 hours (0.079, 0.079).
- **Same inputs:** statsforecast's seasonal naive median equals the last season of the context we scored against
  in 650 of 650 October forecasts.
- **Outliers:** dropping the 5 series with the largest ratio in either direction leaves every verdict where it was
  (grid 0.993 and 0.895, pageviews 0.904 and 0.947 against Chronos-2 and TimesFM-2.5).
- **Recount:** we recomputed all 3,600 per-series MASE values for the October and September windows from the raw
  forecasts with separate code (largest relative difference 4.5e-16), and every ratio above from those values,
  with 0 disagreements ([`reproduce/recount/recount.txt`](reproduce/recount/recount.txt)).

All numbers come from [`reproduce/out/score-all.json`](reproduce/out/score-all.json) and
[`reproduce/out/checks-fresh.json`](reproduce/out/checks-fresh.json).

## Limits

- One week of October targets (7 grid forecast days, 2 pageview forecast days) and two kinds of data.
- Univariate and zero-shot only. Timestral, Chronos-2 and the grid operators can use weather or calendar inputs;
  we gave none.
- Library defaults and a 2,048-hour / 512-day context for every model, although Timestral accepts much longer.
- The pageview set is August's most-viewed English Wikipedia articles, including some pages whose traffic was
  decaying after news.
- EIA may revise recent "Adjusted" demand values; our copy is in `reproduce/data/frames.json.gz`.
- TimesFM-3 was not run (its weights are under a non-commercial licence), so this does not test Mistral's
  comparison with TimesFM-3.
- CPU times are from one machine and are only indicative.

## Licences

The Timestral weights are under a "Modified MIT" licence ([Timestral-209M
LICENSE](https://huggingface.co/mistralai/Timestral-209M/blob/main/LICENSE)). Clause 2: you may not exercise any
rights under it if the global consolidated monthly revenue of your company, or your employer's, exceeded $20
million in the preceding month. The Timestral code is Apache-2.0; Chronos-2, Chronos-2-small and TimesFM-2.5 are
Apache-2.0.

## Rerun it

[`reproduce/README.md`](reproduce/README.md) has the commands, the exact inputs and the pinned versions.

Sources: [EIA-930 six-month balance file, July–December 2026](https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_BALANCE_2026_Jul_Dec.csv)
(large CSV), [Wikimedia pageviews API](https://wikimedia.org/api/rest_v1/), [mistralai/timestral](https://github.com/mistralai/timestral).

This note was prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai.
