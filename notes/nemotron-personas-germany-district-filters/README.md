# Nemotron-Personas-Germany by district: housing, marital status and age match the census; immigration history is pulled about halfway toward the national average (October 26)

[Nemotron-Personas-Germany](https://huggingface.co/datasets/nvidia/Nemotron-Personas-Germany) is NVIDIA's set of
one million synthetic German adults, released on October 19 under CC BY 4.0. Each record sits in one of Germany's 400
districts (Kreise). The card says the set is "grounded in distributions of self-reported demographic data" from Zensus
2022, and that its fields help researchers in "zeroing in on specific demographics". It also mentions "some necessary
independence assumptions" without listing them.

Filter the set to one district and you want that district's mix, not Germany's average. We compared each district's rate
in the dataset with the census rate for six attributes.

**If you build a regional panel from these personas: housing tenure, marital status, age and one-person households
follow the census from district to district. Immigration history ranks districts in the right order, but its
differences are about half the census's. In all 75 East German districts the dataset's share is above the census share
of people born abroad, at the median twice as high, and the cities with the highest shares come out too low. Where
district-level immigration history matters, reweight that field to the census or leave it out.**

## Results

Census range and dataset range are the lowest and highest district rates. ρ is the rank correlation across the 400
districts. The slope says how far the dataset's district rate moves per point of the census rate: 1 means the full
district differences, 0 means the same rate everywhere. Brackets are 95% bootstrap intervals.

| Attribute | Census range | Dataset range | ρ | Slope |
|---|---|---|---|---|
| Lives in an owner-occupied home | 14.9–73.0% | 18.3–79.4% | 0.99 | 1.05 [1.03, 1.06] |
| Divorced, among the ever married | 8.2–19.6% | 7.8–22.0% | 0.87 | 1.05 [0.99, 1.11] |
| Widowed, among the ever married | 8.8–17.2% | 8.1–18.0% | 0.84 | 0.94 [0.89, 1.00] |
| Aged 60 or over, among those 20 or over | 26.3–49.3% | 25.9–51.0% | 0.95 | 0.99 [0.97, 1.02] |
| One-person household | 29.9–58.6% of households | 16.2–38.7% of people | 0.95 | not comparable |
| Immigration history | 4.2–41.9% born abroad | 11.6–38.6% | 0.92 | **0.53 [0.51, 0.56]** |

- The first four hold within each state (slopes 0.91 to 1.06 after removing state averages) and beyond what each
  district's age mix explains (0.92 to 1.05 for tenure, divorce and widowhood). The dataset is not just copying state
  averages or age structure.
- One-person households: the census counts households, the dataset counts people, so only the ranking compares. It
  matches (ρ 0.95).
- Immigration history stays at about half within states (0.58) and after allowing for age (0.51).

## Where immigration history goes wrong

The national figures nearly agree: 20.2% of the dataset's adults have an immigration history, and 18.8% of everyone
in the census grid was born abroad. The gap is at the two ends: districts with few people born abroad get too many,
and districts with many get too few.

| District | Census, born abroad (all ages) | Dataset (18 and over) |
|---|---|---|
| Erzgebirgskreis | 4.2% | 14.0% |
| Bautzen | 5.4% | 12.6% |
| Landkreis Leipzig | 5.5% | 12.3% |
| Dresden | 11.6% | 17.3% |
| Median of the 75 East German districts | 7.3% | 14.5% |
| Berlin | 24.9% | 23.9% |
| Frankfurt am Main | 35.7% | 31.1% |
| Ingolstadt | 33.5% | 24.2% |
| Pforzheim | 39.3% | 31.3% |

East German districts are those in Brandenburg, Mecklenburg-Vorpommern, Saxony, Saxony-Anhalt and Thuringia; Berlin
is not counted among them. We picked out these districts after the main test, so the rows describe the gap; they were
not part of the test we set in advance.

**The two sides measure different things, so we checked whether that could explain the East German gap.** The open
census grid gives country of birth for all ages. The dataset's field, *Einwanderungsgeschichte*, is the census's term
for people who immigrated themselves or whose parents both did, and the dataset covers people aged 18 and over. In
Zensus 2022, children of immigrants are counted only up to age 18 ([press release No. 47, July 11,
2024](https://web.archive.org/web/20250401225446/https://www.zensus2022.de/EN/News/2022_census_19_percent_of_population_immigrated_to_germany.html)),
so for people aged 20 and over the census's immigration history means born abroad. We therefore compared people
aged 20 and over on both sides, choosing every assumption against our finding:

- **Census, at most:** every person born abroad, of any age, and every person in a grid cell whose birth figures
  Destatis withholds, counted as aged 20 or over and born abroad, then divided only by the people aged 20 or over in
  cells whose age figures are published.
- **Dataset, at least:** every 18- or 19-year-old record counted as having an immigration history, and removed.

Even so, the dataset's share is higher in 72 of the 75 East German districts. In Erzgebirgskreis it is at least
12.3%, against at most 5.3% in the census; at the median, at least 12.9% against at most 9.5%. The exceptions are
Potsdam, Prignitz and Weimar. These bounds apply to the grid cells we assign to each district by their centre, and
they don't allow for the small changes Destatis makes to grid cells for confidentiality. We have no such bound for
the cities whose shares come out too low, so read those rows as an all-ages comparison only. The census database has
the exact table by district, but downloading it needs a registered account, which we didn't use.

## What this does not test

- Combinations within a district, such as immigration history by housing tenure in Berlin.
- Education, employment, occupation and the persona text.
- Other countries' Nemotron-Personas sets.
- Revisions other than `1285ad18`. The data files on the dataset's main branch were the same on October 26.

## What we ran

Census side: the Zensus 2022 1 km grid tables published by Destatis, with each cell assigned to the district that
contains its centre (0.14% of people, in cells whose centre lies outside every district, go to the nearest one).
Dataset side: the structured fields of all one million records, with the 400 district names mapped to official
district codes; the run stops unless every name maps to exactly one district. A control checks that each district's
share of records matches its share of the census population (ρ 0.998, slope 1.00).

We wrote down the method and the decision rule before computing any dataset rate. Our advance guesses were wrong for
three of the six attributes: we expected immigration history to hold and housing tenure to be flattened. The named
districts, the bounds and the definition check came after the result. One run on our own machine; nobody else has
reproduced it.

## Files

[`reproduce/`](reproduce/) has the container definition, the three scripts, our per-district counts on both sides,
the scores, a short standard-library script that recomputes every number above, and
[`immigration-by-district.csv`](reproduce/out/immigration-by-district.csv) with all 400 districts. See
[`reproduce/README.md`](reproduce/README.md) for commands, inputs and licences.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai. We will publish dated corrections here.
