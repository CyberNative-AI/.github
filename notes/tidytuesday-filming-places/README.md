# Most titles have one recorded filming place

[Chart](filming-places.png) · [Accessible description](filming-places.alt.txt) · [Python script](filming_places.py)

Among titles with at least one recorded filming place, **73.0% of films** (7,809 of 10,694) and **68.4% of TV series** (985 of 1,440) have exactly one. TV series spread a little wider: 6.0% of them have five or more places, against 4.3% of films. The chart uses four bins to keep the common values visible on a phone. The 5+ bin includes all titles with at least five distinct recorded place IDs.

| Distinct places per title | Films (10,694) | TV series (1,440) |
| --- | ---: | ---: |
| 1 | 7,809 (73.0%) | 985 (68.4%) |
| 2 | 1,542 (14.4%) | 245 (17.0%) |
| 3–4 | 880 (8.2%) | 124 (8.6%) |
| 5+ | 463 (4.3%) | 86 (6.0%) |

Each percentage uses the total number of titles of the same type with at least one linked place in the release. Percentages are rounded independently. A title is a Wikidata production ID. A distinct place is a Wikidata location ID. The released data contains Wikidata filming location (P915) links to sites and towns. Scene details and complete shooting histories are outside its scope. The comparison describes this release and its coverage.

The three tables contain 12,134 production IDs, 7,128 place IDs and 20,283 unique production–place pairs. There are no duplicate pairs, duplicate IDs in either lookup table, conflicting production types, missing join keys, or unmatched links. The pair counts agree with both released lookup-table totals. Optional fields such as year and place Wikipedia URL have blanks and do not enter the comparison.

## Rebuild the chart

With Python 3.11 or later, run these commands from this folder. The `style/` folder next to the script holds the colours and fonts the chart uses.

```sh
python -m pip install matplotlib==3.10.8
python filming_places.py
```

The script fetches the three CSVs from [the pinned release](https://github.com/rfordatascience/tidytuesday/tree/4a0165750d641152637f067e8f14856b366c048a/data/2026/2026-11-24), prints the audit, and writes the PNG and description. To use local copies of those CSVs, pass `--data /path/to/csv-folder`.

Data from [Movie Scene Map (CC0)](https://moviescenemap.com/data/), built from Wikidata and curated by Flightmussy for [TidyTuesday, 24 November 2026](https://rfordatascience.github.io/tidytuesday/data/2026/2026-11-24/readme.html). Font licenses are included with the fonts.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents.
