# Socrata's SODA1 CSV goes away December 16. The documented replacement turns numbers into text.

> **Correction — October 9, 2026:** The pandas and R helpers below remove every `:`-prefixed column, including computed-region columns. On San Francisco's film-location dataset (`yitu-d5am`), this drops three columns present in SODA1: `SF Find Neighborhoods`, `Analysis Neighborhoods` and `Current Supervisor Districts`. Our 21-dataset header-match result below remains a result for that sample; these helpers do not preserve the SODA1 schema for every dataset. If your pipeline uses computed-region columns, do not use the helpers unchanged. Save the old column names while SODA1 is available and compare them with the replacement before migrating.

If a script, notebook or dashboard of yours downloads

```
https://{portal}/api/views/{dataset-id}/rows.csv?accessType=DOWNLOAD
```

it has about two months left. Tyler Technologies' Deprecation Roadmap schedules the SODA1 API for removal on December 16, 2026. Its "Using the SODA3 API" article gives a one-line replacement for a full download:

```
https://{portal}/api/v3/views/{dataset-id}/export.csv
```

That swap keeps your column names, but it doesn't always keep your numbers.

## What changed in 120 popular datasets

On October 9, 2026 we downloaded 120 public datasets three ways: SODA1 `rows.csv`, SODA3 `export.csv` and SODA3 `query.csv`. The datasets were drawn at random from the 1,000 most-viewed datasets in Socrata's US catalog and came from 28 portals.

In 65 of the 120 (54%), at least one column that held only plain numbers in the SODA1 file came back from `export.csv` with display formatting. That meant thousands separators in 49 datasets, a dollar sign in 19 and a percent sign in 8. The 65 came from 20 of the 28 portals.

| Dataset | Column | SODA1 `rows.csv` | `export.csv` | `query.csv` |
|---|---|---|---|---|
| Chicago, Current Employee Names, Salaries, and Position Titles | Annual Salary, one employee | `165624.00` | `$165,624.00` | `165624` |
| CDC, Provisional COVID-19 Death Counts by Age in Years | Total deaths, first row | `28159` | `28,159` | `28159` |
| NYC, Open Parking and Camera Violations | Fine Amount | `115.00` | `$35.00` | `35` |

The NYC rows come back in a different order from each endpoint, so that row shows the format, not the same ticket.

Nothing fails when the file loads. A CSV reader just makes those columns text, and the trouble shows up later. With pandas 3.0.6, `df["Total deaths"].sum()` on the CDC export returns the string `'28,15934,5552,477…'`, every value glued together, and no error. In base R 4.4.2, `sum()` on the Chicago salary column stops with `invalid 'type' (character) of argument`.

We weren't the only ones to hit this. On October 8 a contributor to a public freight-safety pipeline [proposed a fix](https://github.com/GoAugment/augment-carrier-audit/pull/97) that avoids the `export.csv` swap, because insurance amounts came back as `"750,000"` instead of `"750000.00"`. The pipeline's type cast would have turned every one into a null, with no error.

None of this is hidden. The same Tyler article says: "Use /query.csv for machine processing which has a standard format across datasets and views, /export.csv for human-readable report which honors the views formatting." The trouble is that the migration section's full-download example points to `export.csv`.

## The other replacement keeps numbers and changes names

`query.csv` added no separators, `$` or `%` to any column that held plain numbers in SODA1, in all 120 datasets. It isn't a drop-in either:

- **Column names** are API field names in 115 of 120: `Total deaths` becomes `total_deaths`. You can't always guess them. In another CDC dataset, `Deaths from All Causes` comes back as `total_deaths`.
- **System columns** such as `:id`, `:version`, `:created_at` and `:updated_at` come first.
- **Dates** change format: `01/01/2020` becomes `2020-01-01T00:00:00.000`. That happened in 59 of the 64 datasets that had `MM/DD/YYYY` columns.
- **Authentication.** Tyler lists the query endpoint as requiring an app token or user credentials. Anonymous requests worked for all 120 datasets on October 9. Don't build on that.

`export.csv` changed some dates too, in 8 of those 64 datasets. In NYC Parks Properties, `07/15/1997 12:00:00 AM` became `1997 Jul 15 12:00:00 AM`.

## Which one to use

- **Your code calculates with the values:** use `query.csv` with an app token, and map the names back.
- **People open the file in a spreadsheet:** `export.csv` is what it's for.
- **SODA2 `/resource/{id}.csv`** also returns plain numbers, and it isn't on Tyler's Deprecation Roadmap. It uses the same field names as `query.csv`, though, and stops at 1,000 rows unless you set `$limit`. Without it, Chicago's employee salaries came back as 1,000 of 32,021 rows, with no error.
- **Before December 16, either way:** save one SODA1 file for each dataset you depend on. After the cutoff you can't download it again to see what changed. Don't count on the full two months, either. On October 8 the same freight-safety pipeline reported HTTP 410 `feature_deprecated` on all 16 of its SODA1 URLs. Ours still returned 200 on October 9.

### pandas

```python
import json
import urllib.request

import pandas as pd


def read_socrata(portal, dataset, app_token=None):
    """Read a Socrata dataset with its SODA1 column names and raw values."""
    with urllib.request.urlopen(f"https://{portal}/api/views/{dataset}.json") as r:
        old_names = {c["fieldName"]: c["name"] for c in json.load(r)["columns"]}
    df = pd.read_csv(
        f"https://{portal}/api/v3/views/{dataset}/query.csv",
        storage_options={"X-App-Token": app_token} if app_token else None,
    )
    df = df.loc[:, ~df.columns.str.startswith(":")]
    return df.rename(columns=old_names)


df = read_socrata("data.cdc.gov", "3apk-4u4f", app_token="YOUR_APP_TOKEN")
df["End Date"] = pd.to_datetime(df["End Date"])  # dates arrive as ISO text
```

### R

```r
read_socrata <- function(portal, dataset, app_token = NULL) {
  meta <- jsonlite::fromJSON(sprintf("https://%s/api/views/%s.json", portal, dataset))
  old_names <- setNames(meta$columns$name, meta$columns$fieldName)
  tmp <- tempfile(fileext = ".csv")
  download.file(sprintf("https://%s/api/v3/views/%s/query.csv", portal, dataset), tmp,
                quiet = TRUE, headers = if (!is.null(app_token)) c("X-App-Token" = app_token))
  df <- read.csv(tmp, check.names = FALSE)
  df <- df[, !startsWith(names(df), ":"), drop = FALSE]
  names(df) <- old_names[names(df)]
  df
}

df <- read_socrata("data.cdc.gov", "3apk-4u4f", app_token = "YOUR_APP_TOKEN")
df[["End Date"]] <- as.Date(df[["End Date"]])
```

We ran both functions without a token on October 9. On 21 datasets from 16 portals, the renamed `query.csv` header matched the SODA1 header exactly. On the 9 of those small enough to download whole with pandas (3 with R), the row counts matched, every numeric SODA1 column stayed numeric and every column sum was the same. With a made-up token, both versions got HTTP 403, so the token does get sent. We haven't tested a real token, or whether `query.csv` returns every row of a very large dataset. Tyler's roadmap doesn't schedule the `/api/views/{id}.json` metadata route for removal, but it doesn't promise to keep it either; if it goes, the helper fails with an error rather than silently.

### If you stay on export.csv

```python
def to_number(s):
    return pd.to_numeric(s.astype("string").str.replace(r"[$,%]", "", regex=True))

df["Total deaths"] = to_number(df["Total deaths"])
```

```r
to_number <- function(x) as.numeric(gsub("[$,%]", "", x))
```

Clean only the columns you mean to be numbers, because years and IDs pick up separators too. In the US DOT rail crossing inventory, a year column reads `2,019`. And there are two things cleaning can't undo:

- **Percent scale differs by dataset.** In 3 of the 8 datasets with percent columns, SODA1 held a fraction and the export shows it multiplied by 100. CDC's `Percent of Expected Deaths` is `0.97` in SODA1 and `97%` in the export. In others, `94.01` just becomes `94.01%`. Compare one value against your saved SODA1 file before you decide whether to divide by 100.
- **Rounding follows the display.** In Chicago's COVID-19 cases by ZIP code, one weekly case rate is `14` in SODA1 and `15` in the export (4 cases in a population of 27,519, so 14.5 per 100,000).

In the 31 affected datasets small enough to compare in full, the cleanup restored SODA1's exact values in 128 of 133 broken columns. Rounding and percent scale account for the other 5.

## How we measured, and what this doesn't show

- **Sample:** 120 datasets, taken in seeded random order from the 1,000 most-viewed datasets in the Socrata US catalog (Discovery API, sorted by total page views), October 9, 2026, across 28 portals. These are popular datasets, which isn't the same as the datasets code downloads most.
- **"Turns into text"** is a pattern test on the values (plain number versus separators, `$` or `%`), not a pandas or R load of every file. The pandas and R results above come only from the datasets named.
- **Size cap:** each download stopped at 5 MB. Among the 58 datasets where neither file hit the cap, 31 (53%) broke, so the cap isn't what drives the result. Row counts were compared on those 58; all matched.
- **Live data:** the three files for each dataset were fetched one after another, from datasets that keep changing.
- **Checks after the main run:** we counted date formats, `query.csv` number formats (columns matched by position), percent scale and the cleanup results afterwards, on the same files. Date checks used the first 2,000 rows of each column.
- **Not reproduced:** we ran the study once, and no one else has reproduced it yet.
- **Sunset header:** SODA1 responses carry `Sunset: Tue, 22 Dec 2026`, six days after the documented date. Plan for December 16.

Sources: Tyler Technologies, [Deprecation Roadmap](https://support.socrata.com/hc/en-us/articles/360008097514-Deprecation-Roadmap) (edited September 17, 2026) and [Using the SODA3 API](https://support.socrata.com/hc/en-us/articles/43491231777047-Using-the-SODA3-API) (edited October 9, 2026).

Published by CyberNative AI LLC. Prepared with AI assistance. Corrections: hello@cybernative.ai.
