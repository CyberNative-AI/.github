# dst-check: test your installed JavaScript scheduler across a clock change

[Download dst-check.zip](https://github.com/CyberNative-AI/.github/raw/refs/heads/main/tools/dst-check/dst-check.zip), unzip it, then run this from a project that has `cron` installed:

```sh
node ../dst-check/bin/dst-check.cjs "0 0 3 * * *" Europe/Berlin --library cron
```

Adjust the path to the extracted checker. It runs the scheduler version in **your project's `node_modules`** under a controlled clock across the next two timezone offset changes. The report shows UTC and local callback times, labels them `ok`, `MISSED`, `DUPLICATED` or `SHIFTED`, and gives a consequence and configuration hint. This is a controlled-time check, not a production run.

Requires Node 20 or newer; tested on Node 22.23.2, ICU 78.2, tzdata 2026a. Node 20 has not been independently exercised. The checker bundles its clock dependency and needs no install or network access to run; your project must already have the selected scheduler installed.

## Try it in an empty project

Start in the directory where you saved the zip:

```sh
unzip dst-check.zip
mkdir dst-check-demo
cd dst-check-demo
npm i --registry=https://registry.npmjs.org --ignore-scripts --no-audit --no-fund --save-exact cron@4.4.0
node ../dst-check/bin/dst-check.cjs "0 0 3 * * *" Europe/Berlin --library cron --version 4.4.0 --year 2026
```

At the Berlin fall-back on 25 October 2026, this version fires at `01:00Z` (02:00 local, `SHIFTED`) and `02:00Z` (03:00 local, `ok`). The first callback is outside the requested 03:00 schedule. [Five worked examples](examples/README.md) cover that case, New York's spring gap, Melbourne's repeated hour and a UTC control.

## Choose the project and window

Supported libraries: `cron`, `node-cron` and `node-schedule`. Croner and `cronosjs` are not supported in this version.

The current directory is the default project. `--project DIR` selects another project; `--version X.Y.Z` asserts its installed version. Neither flag downloads a package or chooses a different release. The first output line reports the resolved library and version.

Without `--year`, the checker selects the next two offset changes after the run starts. `--year YYYY` checks every change in that UTC year. The default window covers four elapsed hours before through four hours after each change, with the end excluded. `--before-hours N` and `--after-hours N` each accept whole numbers from 0 to 24; their total must be nonzero and cannot exceed 48 hours.

`--json` returns the full report. Exit code 0 means the requested windows completed, even if the report has warning labels. Exit code 1 means invalid input, a missing package, a version mismatch or an execution/cleanup error.

## Read the calendar rule before the DST labels

The report's `calendarPolicy` declares how the independent reference combines day-of-month and day-of-week. In either day field, `*` or a wildcard with a numeric step of 1 (`*/1`, including `*/01`) is unrestricted:

- If both day fields are unrestricted, every day matches.
- If one is unrestricted, the other day field must match.
- If both are restricted, either day field can match: **day-of-month OR day-of-week**.

This definition follows the expression's spelling. `*/2`, full-domain ranges and lists are not treated as unrestricted merely because their expanded values cover a day field. The remaining numeric fields must also match.

For example, `0 3 */1 * 1` selects Mondays at 03:00 in the reference, just as `0 3 * * 1` does. With `0 3 24 * 1`, both day fields are restricted: the reference includes the 24th of the month **or** a Monday. The tested `node-cron@4.6.0` instead requires day-of-month **and** day-of-week to match, consistent with its [documented AND rule](https://github.com/node-cron/node-cron#cron-syntax). That executed-version result does not establish the behavior of an untested node-cron release.

A `MISSED` row with `reasonCode: CALENDAR_POLICY_DIFFERENCE` identifies a slot included by the OR reference but excluded by an AND calendar. For an untested installed version, an absent callback at such a slot is consistent with the documented rule; it does not verify that version's implementation. **Confirm the intended day rule and re-test the exact expression, timezone and installed version.** A calendar-policy difference alone does not call for UTC, skipped-hour or repeated-hour repair advice. Read any separate DST warnings as well.

## Read the labels as a DST comparison

Separately, `comparisonPolicy` describes the DST baseline: the independently calculated reference skips nonexistent wall-clock slots and uses the **first occurrence** of a repeated wall time. The calendar and DST policies are comparison baselines, not universal scheduler rules or defect verdicts.

- `ok`: one callback matches the expression under that policy.
- `MISSED`: a reference slot had no callback, or an expression-matching local time did not exist. Check its reason: `CALENDAR_POLICY_DIFFERENCE` is a day-rule difference. A nonexistent slot has no UTC instant.
- `DUPLICATED`: callbacks share a repeated local wall time or the same UTC instant.
- `SHIFTED`: a callback's local time does not match the expression.

A library can document a different calendar or DST policy. Read the reason, local time and that library's documentation before changing a job. A `MISSED` or `DUPLICATED` label can reflect the baseline rather than a production defect.

The reference supports numeric five-field cron expressions, or six fields with a literal second of `0`, including lists, ranges and steps. Its day-field rule is declared above. Names for months/weekdays, nicknames, `L`, `W`, `#`, `?`, year fields and sub-minute schedules are not supported.

## Evidence and limits

Tested scheduler versions: `cron@4.4.0` and `cron@4.3.3`, `node-cron@4.6.0`, and `node-schedule@2.1.1`. The [JavaScript scheduler comparison](https://github.com/CyberNative-AI/.github/tree/main/notes/javascript-dst-2026) gives broader measured context. The commands here execute your installed version; a syntax checker and library documentation do not provide that callback trace.

This checker uses controlled fake time, not native timers. Millisecond-sensitive library paths can behave differently in production. Results are evidence for the exact expression, timezone and installed version under this method, not a guarantee of native-timer or production behavior.

Results can change with the library release, Node/ICU/tzdata, process startup, options or transition rules. The tool simulates a trivial synchronous callback within bounded windows. It does not test production uptime, restart/catch-up behavior, callback duration, overlap pressure, persistence, multi-process coordination, host clock behavior or every parser feature. It changes no production process. Test your actual handler and deployment separately.

The configuration hint is general advice, not a tested repair. Moving a job outside the changed hour is insufficient: the Berlin `cron@4.4.0` job configured for 03:00 fired at both 02:00 and 03:00 in this controlled-time check. Re-test the exact expression, timezone and installed library version after any configuration change.

A UTC schedule keeps a fixed UTC cadence; its local fire time changes when the local offset changes and differs across regions. Choose UTC only if that trade-off fits the requirement. If the job must keep a fixed local wall time, use the intended IANA timezone and test that requirement. UTC is not a universal fix for library defects. An idempotency guard can prevent a repeated side effect, but cannot recover a missed run or make an early callback occur at the configured time.

## License and disclosure

The checker is [MIT licensed](LICENSE), Copyright (c) 2026 CyberNative AI LLC. Bundled dependencies keep their own licenses; see [third-party notices](vendor/THIRD-PARTY-NOTICES.md). Scheduler packages are installed separately by the reader and are not in the download.

Prepared with AI assistance. Published by CyberNative AI LLC. Corrections: hello@cybernative.ai.
