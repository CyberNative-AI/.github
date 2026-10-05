# Five dst-check examples in your own scratch projects

[Download dst-check.zip](https://github.com/CyberNative-AI/.github/raw/refs/heads/main/tools/dst-check/dst-check.zip) and extract it with `unzip dst-check.zip`. Each block below starts in the directory containing the extracted `dst-check/` folder and makes a separate empty project. Run with Node 20 or newer; these outputs were tested on Node 22.23.2 (ICU 78.2, tzdata 2026a). Node 20 has not been independently exercised.

Only the `npm i` commands need network access. The checker uses that project's freshly installed package and prints its version. `--version` asserts the pin, and `--year` makes the example independent of today's date. Append `--json` for structured output. `comparisonPolicy` states the DST baseline: skip nonexistent slots and use the first repeated occurrence. `calendarPolicy` states the separate day-field baseline. The labels are comparisons, not universal defect verdicts.

In either day field, `*` or a wildcard with a numeric step of 1 (`*/1`, including `*/01`) is unrestricted. If one day field is unrestricted, the other must match; if both are unrestricted, every day matches. With both restricted, the reference uses **day-of-month OR day-of-week**. Full-domain ranges and lists do not become unrestricted merely by expanding to every value; `*/2` remains restricted.

The tested `node-cron@4.6.0` uses **AND** between restricted day fields, consistent with its [documented day rule](https://github.com/node-cron/node-cron#cron-syntax). That test does not establish behavior for an untested node-cron version. A `MISSED` row marked `reasonCode: CALENDAR_POLICY_DIFFERENCE` belongs only to the OR reference, not an AND calendar. For an untested installed version, the absence is consistent with the documented rule; it is not proof of that implementation. Confirm your intended day rule and re-test the exact expression, timezone and installed version. Calendar-only rows do not call for UTC or DST repair advice; retain any separate DST warnings.

## 1. Berlin: a daily cron callback outside its expression

```sh
mkdir dst-berlin
cd dst-berlin
npm i --registry=https://registry.npmjs.org --ignore-scripts --no-audit --no-fund --save-exact cron@4.4.0
node ../dst-check/bin/dst-check.cjs "0 0 3 * * *" Europe/Berlin --library cron --version 4.4.0 --year 2026
cd ..
```

The report prints `cron@4.4.0`. At the 25 October fall-back, the callbacks are `2026-10-25T01:00:00.000Z` (02:00 local, `SHIFTED`) and `2026-10-25T02:00:00.000Z` (03:00 local, `ok`). The first callback does not match the requested 03:00 expression.

## 2. New York: nonexistent half-hour slots

```sh
mkdir dst-new-york-half-hour
cd dst-new-york-half-hour
npm i --registry=https://registry.npmjs.org --ignore-scripts --no-audit --no-fund --save-exact node-cron@4.6.0
node ../dst-check/bin/dst-check.cjs "*/30 * * * *" America/New_York --library node-cron --version 4.6.0 --year 2026
cd ..
```

The report prints `node-cron@4.6.0`. At the 8 March spring jump, local 02:00 and 02:30 are `MISSED` with no UTC instant because those wall times do not exist. Observed callbacks around the gap have real UTC instants and local offsets.

## 3. New York: a fixed 02:30 job shifts to 03:30

```sh
mkdir dst-new-york-fixed
cd dst-new-york-fixed
npm i --registry=https://registry.npmjs.org --ignore-scripts --no-audit --no-fund --save-exact node-schedule@2.1.1
node ../dst-check/bin/dst-check.cjs "30 2 * * *" America/New_York --library node-schedule --version 2.1.1 --year 2026
cd ..
```

The report prints `node-schedule@2.1.1`. On 8 March there is no 02:30 local instant. The callback occurs at 03:30 local (`SHIFTED`), and the missing 02:30 wall slot is shown separately as `MISSED`.

## 4. Melbourne: two occurrences of each repeated half hour

```sh
mkdir dst-melbourne
cd dst-melbourne
npm i --registry=https://registry.npmjs.org --ignore-scripts --no-audit --no-fund --save-exact cron@4.4.0
node ../dst-check/bin/dst-check.cjs "*/30 * * * *" Australia/Melbourne --library cron --version 4.4.0 --year 2024 --before-hours 1 --after-hours 2
cd ..
```

The report prints `cron@4.4.0`. In the window around the 7 April 2024 overlap, it fires six times, from 6 April `15:00Z` through `17:30Z`. Local 02:00 and 02:30 each occur twice and are labelled `DUPLICATED`; 03:00 and 03:30 are `ok`. The year option also includes October's spring jump, with missing 02:00 and 02:30 slots labelled `MISSED`.

## 5. UTC: no offset transition

```sh
mkdir dst-utc
cd dst-utc
npm i --registry=https://registry.npmjs.org --ignore-scripts --no-audit --no-fund --save-exact node-cron@4.6.0
node ../dst-check/bin/dst-check.cjs "0 9 * * 1-5" Etc/UTC --library node-cron --version 4.6.0 --year 2026
cd ..
```

The report prints `node-cron@4.6.0`, says there is no offset transition in 2026 for `Etc/UTC`, and returns no transition-window rows. This is a control for transition detection, not a test of weekday job execution.

All five examples use controlled time and a trivial callback. They do not establish production behavior or validate an application's side effects. Moving outside the changed hour is insufficient for the Berlin early-fire case; re-test the exact expression, timezone and installed version after a change. UTC keeps UTC cadence while local fire times can change with the offset; choose it only if that fits the requirement. [Full syntax, policy and coverage limits](../README.md).
