# GBIF's iNaturalist data has about 8,700 extra records on clock-reset dates. None has a GBIF date flag.

iNaturalist users have been correcting observations dated 31 December 1969 by hand for years. In a [forum thread](https://forum.inaturalist.org/t/86827) opened on 14 October 2026 they are doing it again, for 1 January 1970 too; both dates are the Unix clock's zero in local time. On 15 October iNaturalist staff [wrote](https://forum.inaturalist.org/t/86827/28) that the new ones come from Seek, which gives an imported photo without a date the date 31 December 1969, and that they had filed a bug report.

GBIF republishes iNaturalist's research-grade observations as one dataset, and researchers download them from there. We counted the records in that dataset on twelve dates that a reset clock or an empty date field can produce, and compared each date with the days around it and with the same day in other years. Six dates stand out. The two largest are not the Unix dates.

## Check a download or a dataset

```sh
curl -sO https://raw.githubusercontent.com/CyberNative-AI/.github/main/notes/gbif-clock-reset-dates/sentinel_dates.py
python3 sentinel_dates.py file occurrence.txt                          # count them in a GBIF download
python3 sentinel_dates.py file occurrence.txt --exclude-to clean.txt   # and copy the other rows to a new file
python3 sentinel_dates.py file occurrence.txt --dates 1980-01-01,2000-01-01 --midnight   # times 00:00-00:19 only
python3 sentinel_dates.py gbif                                         # iNaturalist research grade, live
python3 sentinel_dates.py gbif --dataset <datasetKey>                  # another dataset, or "all"
python3 sentinel_dates.py clock                                        # clock times on those dates, live
```

It uses only the Python standard library. `file` reads a GBIF simple CSV download or the `occurrence.txt` of a Darwin Core Archive (both are tab-separated) and counts rows whose event date is one of the eight dates where we found an excess; `--dates` takes your own list. `gbif` asks the public GBIF API about 250 questions and takes a few minutes; `clock` reads about 9,000 records in about 60 requests.

## What we found

GBIF's iNaturalist research-grade dataset ([`50c9509d…`](https://www.gbif.org/dataset/50c9509d-22c7-4a22-a47d-8c48425ef4a7)), snapshot of 13 October 2026, read on 16 October:

| Date | What can produce it | Records | Days around it (median) | Same day, other years (median) | Excess |
|---|---|---:|---:|---:|---:|
| 2000-01-01 | camera clock reset | 3,280 | 43 | 158 | **3,122** |
| 1980-01-01 | DOS/FAT timestamp zero | 3,138 | 6 | 65 | **3,073** |
| 1970-01-01 | Unix time 0, UTC and east | 1,240 | 1 | 10 | **1,230** |
| 1969-12-31 | Unix time 0, west of UTC | 1,086 | 1 | 0 | **1,085** |
| 1900-01-01 | Excel 1900 system, day 1 | 91 | 0 | 1 | **90** |
| 1899-11-30 | "day 0 of month 0" | 67 | 0 | 0 | **67** |
| 2000-12-31, 2001-01-01, 1980-01-06, 1904-01-01, 1899-12-31, 1899-12-30 | Apple, GPS, Mac and Excel zero dates | 0 to 153 | | | none |

"Days around it" is the seven days either side, which can cross into the previous year; "same day, other years" is one to three years either side. Both leave out the other dates in the table. A date counts when it has at least five times both medians and at least 20 records more than the larger one; the excess is the count minus that larger median. The six dates add up to 8,667. Each of 1980-01-01 and 2000-01-01 has more excess records than the two Unix dates together. [`run-inat.txt`](run-inat.txt) is the full output.

**None of them has a GBIF date flag.** In this dataset, not one record on the twelve dates carries a GBIF date issue (`RECORDED_DATE_INVALID`, `_UNLIKELY` or `_MISMATCH`). GBIF's [issue list](https://api.gbif.org/v1/enumeration/basic/OccurrenceIssue) has no flag for a default or first-of-year date. The Atlas of Living Australia flags `FIRST_OF_YEAR`, `FIRST_OF_MONTH` and `FIRST_OF_CENTURY` ([codes](https://biocache-ws.ala.org.au/ws/assertions/codes)), which cover the January 1 dates but not 1969-12-31 or 1899-11-30.

**It matters most for old dates.** The dataset has 87,048 records dated 1950 to 1989. 5,464 of them, 6.3%, are on 1969-12-31, 1970-01-01 or 1980-01-01.

## On 1980-01-01 and 2000-01-01, most records are timed just after midnight

A reset clock would also put the time of day near midnight. We read the observation time of every record on the two dates and on the seven days either side of each:

| Date | Records | Time 00:00 to 00:19 | Days around it: share at 00:00 to 00:19 |
|---|---:|---:|---:|
| 1980-01-01 | 3,138 | **2,757 (88%)** | 4 of 157 (2.5%) |
| 2000-01-01 | 3,280 | **2,402 (73%)** | 24 of 785 (3.1%) |

Together, 5,159 records on the two dates are timed 00:00 to 00:19. How many of them would be genuine depends on the baseline. At the rate of the days around them, which we chose before reading the two dates, it is about 180 (3.5%). At the rate of 1 January in nearby years, 29 of 476 (6.1%) around 1980 and 139 of 879 (15.8%) around 2000, it is about 710 (13.8%). Those nearby New Year's Days may have clock resets of their own, more people out at midnight, or both; we did not establish which. On the days-around baseline, the midnight window holds a modeled excess of 4,979 records, about 80% of the two dates' estimated whole-day excess of 6,195. This is a concentration on two days, not a finding about which individual records are wrong. [`run-clock.txt`](run-clock.txt) is the output for the days-around baseline.

The Unix dates look different. On 1969-12-31, 1,001 of the 1,086 records have a time between 16:00 and 19:59; on 1970-01-01, 938 of 1,240 are between 01:00 and 02:59. These hour clusters are consistent with UTC-midnight offsets (UTC−8 to UTC−5, and UTC+1 and UTC+2); we did not validate each record's time zone or the reset mechanism.

## iNaturalist's own filter removes more of 1969 than of 1980 or 2000

| Date | iNaturalist, all observations (16 Oct) | Research grade (16 Oct) | In GBIF (13 Oct snapshot) |
|---|---:|---:|---:|
| 1969-12-31 | 13,806 | 1,075 | 1,086 |
| 1970-01-01 | 7,287 | 1,305 | 1,240 |
| 1980-01-01 | 9,276 | 4,136 | 3,138 |
| 2000-01-01 | 10,653 | 4,166 | 3,280 |
| 1899-12-31 | 2,566 | 2 | 2 |

Observations need research grade and an open licence to reach GBIF. 8% of the 1969-12-31 observations on iNaturalist are research grade; for 2000-01-01 it is 39% and for 1980-01-01 45%. We did not study why. The iNaturalist counts were read during the volunteer clean-up and are changing.

## Outside iNaturalist

Across all GBIF datasets, one date stands out after the largest dataset on it is removed: 1899-12-30, day zero of the date format used by Access and by Windows programs (OLE Automation), where an empty date exported from a spreadsheet or a database can end up. It has 26,441 records, 66 times the days around it; without its largest dataset, 10,714 remain, 27 and 36 times the two medians.

January 1 dates are much larger outside iNaturalist (for example 369,312 records on 1970-01-01, 302,344 of them from one dataset), but most of each comes from a single dataset, and without it they are close to the same day in other years. They are probably publishers' placeholders for an unknown date, a different problem we did not establish. On every date in the table, at most 0.5% of records across all GBIF datasets carry a date issue, except 1980-01-06, GPS week 0 (6.5%). [`run-all.txt`](run-all.txt) has the counts.

## What to do with a download

- **Before a phenology, first-arrival or historical-baseline analysis,** count these dates in your download. A thousand records on one day in 1980 changes a decade where the dataset is thin.
- **Excluding whole days drops genuine records.** On 2000-01-01 the same day in other years has a median of 158 records, so roughly 160 of the 3,280 may be real New Year's Day observations. `file occurrence.txt --dates 1980-01-01,2000-01-01 --midnight --exclude-to clean.txt`, with a new file name, removes only the rows on those two dates timed 00:00 to 00:19 and copies everything else. About 3.5% of the removed rows are expected to be genuine on the days-around baseline, about 13.8% on the nearby-years baseline. Without `--dates`, `--midnight` still removes the other six default dates whole. A photo or its metadata may help assess an individual record; we did not measure how often.
- **Publishers** can run `gbif --dataset <their datasetKey>` on their own data.

## Limits

- An excess is an estimate for a whole day, not proof about any record. Some records on these dates are genuine.
- "What can produce it" says where such a date can come from. We did not trace any record to its device or software.
- GBIF re-indexes the iNaturalist dataset weekly, and iNaturalist volunteers are fixing dates now, so later runs will give different counts.
- Not covered: wrong dates that are not one of these twelve, other aggregators, and whether any published study used these records. The clock counts cover only GBIF's iNaturalist research-grade dataset.
- The clock time is read as written in the record. Some records carry a time-zone offset, and we did not convert it. The 3.5% assumes that just after midnight on New Year's Day is no busier for observers than on the nights around it. On 1 January in nearby years the midnight share is higher (6.1% and 15.8%), which gives 13.8%. Neither figure is an observed error rate.
- A second analyst reran the research code against the same GBIF snapshot (13 October) and got identical results. That checks the pipeline, not how the counts change over time. The script published here was written separately from the research code and gives the same iNaturalist table.
- The clock counts come from one reading on 16 October. The research code and the script published here were written separately and gave the same counts. Nobody has rerun them.

Files: [`sentinel_dates.py`](sentinel_dates.py) (the counts), [`test_sentinel_dates.py`](test_sentinel_dates.py) (tests for `file`, no network), [`run-inat.txt`](run-inat.txt), [`run-all.txt`](run-all.txt), [`run-clock.txt`](run-clock.txt), `SHA256SUMS`.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai. We publish
corrections as dated notes on this page.
