> Published copy of the protocol we wrote and froze before any forecast for the October or September windows was
> produced. Changes for publication only: an internal owner line, internal tool and directory names removed, and
> first person changed to "we". One date in it is imprecise: 2026-10-14 08:52 UTC is when the Timestral-209M
> repository was created on the Hugging Face Hub; its first listed commit is 2026-10-15 15:22 UTC. Every October
> target is still later. The protocol text is otherwise unchanged.

# Does Timestral's leaderboard lead survive on data that did not exist when it was trained?

Risk tier 1 (public data, public model weights, CPU only, no API keys).
Status: FROZEN before any model output on the FRESH or PRE windows was produced or inspected.

## Why now / decision
Mistral released Timestral (5M–209M) on 2026-10-14/15 and claims first place among zero-shot models on
GIFT-Eval, TIME and fev-bench (209M GIFT-Eval MASE 0.658 vs TimesFM-3 0.667 vs Chronos-2 0.698; margins of
1–6 %). The release mentions post-training on "a mix of real and synthetic data" with no cutoff or dataset list
(open question mistralai/timestral#3, unanswered). Libraries (sktime, darts, TimeCopilot v0.0.39) are adding it
this week; HN commenters (621-point thread) asked how it compares with AutoARIMA / seasonal naive and how to
backtest without leakage. A practitioner choosing a CPU forecaster this week needs to know whether the lead holds
on targets that cannot be in any training set, and whether the 40x smaller model is enough.

Decision changed: recommend Timestral-209M vs a smaller size vs an Apache-licensed alternative (Chronos-2,
TimesFM-2.5) vs a classical baseline for hourly grid demand and daily web-traffic style series.

## Leak-free by construction
All FRESH targets are dated on or after 2026-10-16 00:00 UTC, after the weights were uploaded (HF createdAt
2026-10-14T08:52Z). Contexts may contain older data; only targets matter for leakage.

## Frames (data/frames.json, built by src/prep.py, sha256 in FROZEN.sha256)
- **E — US grid demand.** EIA-930 six-month balance files 2026 Jan–Jun and Jul–Dec (Jul–Dec Last-Modified
  2026-10-23 14:41 GMT), column `Demand (MW) (Adjusted)`, hourly, UTC end-of-hour stamps. Inclusion: every
  target hour present and > 0 in every window (FRESH, PRE, PILOT), ≤ 5 % missing context per window, median
  ≥ 100 MW. Result: 50 balancing authorities kept, 12 excluded (reasons recorded in frames.json).
  Context 2,048 h, horizon 24 h, season m = 24. Origins 00:00 UTC daily: FRESH 10-16 … 10-22 (7), PRE 09-16 …
  09-22 (7). Reference (not equal information, uses weather): the BA's own `Demand Forecast (MW)` at the target
  hours, where complete.
- **W — Wikipedia daily pageviews.** en.wikipedia top-1000 articles of August 2026 (all-access), in rank order,
  skipping namespaced pages/Main_Page, keeping the first 150 with complete daily user-agent views 2024-01-01 …
  2026-10-23 and positive targets. Context 512 d, horizon 7 d, m = 7. FRESH origins 10-16 and 10-17; PRE 09-16
  and 09-17.
- PILOT window (08-10) is plumbing only; it is not analysed.

## Models (pinned; src/install.sh; all inference CPU, 6 threads, network none)
Timestral-5M bdd20cfc, -28M 180698bb, -209M 9874d252 (code mistralai/timestral a534bdbd; library defaults:
symmetric averaging on, non-negative clip on); Chronos-2 (amazon/chronos-2 29ec3766) and Chronos-2-small
(autogluon/chronos-2-small ddec0131), chronos-forecasting 2.3.2 defaults; TimesFM-2.5 (google/timesfm-2.5-200m-
pytorch 1d952420, timesfm 3.0.2, model-card config: normalize_inputs, continuous quantile head, flip invariance,
infer_is_positive, fix_quantile_crossing; max_context = frame context); statsforecast 2.1.1 SeasonalNaive, AutoETS,
AutoARIMA (season m; W only: the pilot fit did not finish 50 hourly E tasks in 11 min, so E would take hours; dropped for E before freezing). TimesFM-3 is excluded: its weights are under a non-commercial licence.
Every model receives identical context arrays (last `ctx` values, gaps linearly interpolated).

## Metrics
Point = median (q0.5; statsforecast point forecast). Per task MASE = mean |y − median| / in-context seasonal
naive MAE (lag m). Per series: mean over origins. Headline per model = geometric mean over series of
MASE / MASE(SeasonalNaive). Pairwise A/B = geometric mean of per-series MASE ratio with a 95 % series-bootstrap CI
(2,000 resamples, seed 16235). Secondary: mean scaled WQL over q0.1…0.9 (not for SeasonalNaive/EIA reference).

## Pre-registered questions and rules (per domain, FRESH window)
- **H1 (claim):** Timestral-209M vs Chronos-2 and vs TimesFM-2.5. A_BETTER if CI upper < 1; B_BETTER if CI
  lower > 1; else TIE. The claim "holds" on a domain only with A_BETTER against both.
- **H2 (practitioner):** Timestral-209M vs the domain's classical comparator (E: MSTL with daily+weekly
  seasonality, statsforecast default trend AutoETS; W: AutoETS) and vs SeasonalNaive, same rule; "clearly worth
  it" needs ratio ≤ 0.90 and A_BETTER against both.
- **H3 (size):** Timestral-5M / Timestral-209M ratio. "Small is enough" if ratio ≤ 1.05.
- **Exploratory L (leak probe), no decision:** difference-in-differences of log(T209/X) PRE minus FRESH for X in
  Chronos-2, TimesFM-2.5, AutoETS. Flag only if the DiD ratio < 1/1.10 with CI upper < 1, worded as "larger
  advantage on the window that could be in training", never as proof of leakage (PRE and FRESH also differ in
  season/weather).
- Reported, not ruled: AutoETS on E, AutoARIMA (W), Timestral-28M vs Chronos-2-small, EIA BA forecast reference, CPU wall time.

## Ruling for the whole experiment
- CHANGE if H1 is not "holds" on at least one domain, or H2 is not "clearly worth it" on at least one domain
  (the public claim would mislead that practitioner choice).
- CONTINUE-NO-CHANGE if H1 holds and H2 clearly worth it on both domains.

## Pre-freeze pilot (PILOT window 2026-08-10 only, plumbing; disclosed)
All models ran with finite output. Two changes made after the pilot and before freezing: (1) AutoARIMA dropped for
E (did not finish 50 hourly tasks in 11 min); (2) MSTL added as E's classical comparator because AutoETS (m=24)
scored 2.05x SeasonalNaive on the pilot window, a straw baseline; MSTL scored 0.70x. We saw the pilot table for all
models (Timestral-209M 0.51, Chronos-2 0.53 on E; 0.54 vs 0.58 on W); the pilot window is not analysed.

## Our pre-freeze forecast (written before any FRESH/PRE output)
H1: TIE vs both on E (p .55) and on W (p .6); B_BETTER on some pair (p .15). H2: E Timestral clearly beats AutoETS
(p .6), beats SeasonalNaive (p .8); W smaller margins, TIE vs AutoETS (p .5). H3: ratio ~1.04–1.08. L: no flag (p .8).
H2 E vs MSTL: Timestral clearly better (p .7). Expected ruling: CHANGE (p .7).

## Resources, abort, teardown
CPU Docker (6 CPUs, 12 GiB, network none, read-only env/weights/source, writable
output directory only). Ceiling: 2 h wall for FRESH+PRE. Abort: a model whose output has any
non-finite value or fewer tasks than the frame is recorded INVALID for that model (scorer asserts); AutoARIMA (W) not
finished within the ceiling is reported as INCOMPLETE, not a loss. Teardown: `--rm` containers.

## Limitations (known before running)
One week of FRESH targets; two domains; zero-shot univariate only (no weather covariates, which Timestral and the
EIA reference can use); library-default inference settings; context capped at 2,048 h / 512 d for every model
although Timestral accepts 32k; Wikipedia frame selected from August popularity (evergreen, high-traffic pages).
Executed by us on our hardware: "Executed", not independently reproduced.
