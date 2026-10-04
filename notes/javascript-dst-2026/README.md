# JavaScript schedulers at the 2026 fall-back: which daily and half-hourly jobs skip or run twice

4 October 2026 · CyberNative AI LLC

A daily job and a half-hourly job can handle the same repeated hour differently—even in the same library. In our controlled-clock checks, `cron@4.4.0` and `node-schedule@2.1.1` ran the repeated half-hour slots twice, while `node-cron@4.6.0` chose different occurrences in London and New York. A daily `cron` job scheduled just after the repeated hour also fired once before its configured time.

These are measured callbacks for pinned versions and inputs, not a forecast for every application. Check your exact schedule before the clock change.

## Dates and schedules covered

[London falls back on 25 October 2026](https://www.gov.uk/when-do-the-clocks-change), repeating 01:00–01:59. [Berlin also falls back on 25 October](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=OJ%3AJOC_2021_149_R_0001), repeating 02:00–02:59. [New York falls back on 1 November](https://www.nist.gov/pml/time-and-frequency-division/popular-links/daylight-saving-time-dst), repeating 01:00–01:59. All times below are local unless marked UTC or `Z`.

For London and New York we tested four schedules: fixed daily `30 1 * * *` (01:30); half-hourly `*/30 * * * *`; hourly `0 * * * *`; and post-fold daily `30 2 * * *` (02:30). The Berlin row is post-fold daily `0 0 3 * * *` (03:00, with a seconds field). Berlin's fixed repeated-hour, half-hourly and hourly rows were **not measured**; do not infer them from London.

“First” and “second” identify the two UTC instants with the same local clock time. Running both is different from invoking a callback twice at one UTC instant.

## What each pinned library did

**`cron@4.4.0`.** The fixed 01:30 daily job ran once, at the first occurrence, in both London and New York. Half-hourly jobs ran both 01:00 occurrences and both 01:30 occurrences; hourly jobs ran both 01:00 occurrences. Post-fold dailies fired early as well as on time: London's 02:30 expression fired at 01:30 and 02:30; New York's 02:30 expression fired at 01:30 and 02:30; Berlin's 03:00 expression fired at 02:00 and 03:00. Each early callback was outside its expression.

**`node-cron@4.6.0`.** In London, the fixed 01:30 job skipped the first occurrence at 00:30Z and ran at the second, 01:30Z. The London half-hourly and hourly rows likewise used the second repeated-hour slots, omitting the first. In New York those three rows used the first occurrence and omitted the second. None of these rows ran a repeated wall slot twice. The post-fold daily ran once at its configured time in London, New York and Berlin.

**`croner@10.0.1`.** Native-timer checks at an accelerated clock rate measured the fixed 01:30 job and half-hourly slots at the first occurrence in London and New York, without running those wall slots twice. Those same checks recorded a sustained loop of timer rearms with negative requested delays around the fold. A short, normal-speed Melbourne spot also observed the loop; it is not a production CPU estimate. Separately, the fake-timer hourly rows used the first occurrence, and post-fold dailies ran once at the configured time in London, New York and Berlin.

**`node-schedule@2.1.1` with `cron-parser@4.9.0`.** The fixed 01:30 job ran once at the first occurrence in London and New York. Half-hourly jobs ran both occurrences of 01:00 and 01:30; hourly jobs ran both occurrences of 01:00. Post-fold dailies ran once at the configured time in London, New York and Berlin. This is evidence for node-schedule using that parser, not an independent validation of the parser.

**`cronosjs@1.7.1`, default DST options.** Fixed 01:30, half-hourly and hourly rows used the first occurrence in London and New York, omitting the second. Post-fold dailies ran once at the configured time in London, New York and Berlin.

We compare against an explicit policy: **skip nonexistent slots and run the first repeated occurrence**. Different documented library policies are not automatically bugs. In particular, running both wildcard slots is distinct from firing a daily job outside its expression. These findings describe the stated versions, startup history and options.

### Croner's development build is a separate result

`croner@11.0.0-dev.2` did not show the negative-delay loop in the accelerated native-timer checks. But it changed timing: the fixed 01:30 target moved to the second occurrence—01:30Z in London and 06:30Z in New York. Half-hourly rows kept the first 01:00 but moved 01:30 to the second occurrence. Counts alone would hide that change.

Those checks used thread-safe libfaketime 0.9.10-2.1 at 600×. Dev.2 callback timing was **not checked at normal clock speed**. This result does not establish a fully validated fix or justify an upgrade recommendation.

## Copy and run two London rows

This small check executes callbacks for the fixed 01:30 and half-hourly rows across four libraries. It reproduces the different repeated-hour choices above. It does **not** reproduce Croner's native-timer loop, Berlin, New York or the post-fold daily rows.

Use an empty directory and Node 22.23.2. The measured environment was ICU 78.2, tzdata 2026a, process `TZ=UTC`. Other dependency or timezone-data versions may change the result.

```sh
npm install --registry=https://registry.npmjs.org --ignore-scripts --no-audit --no-fund --save-exact \
  @sinonjs/fake-timers@15.4.0 cron@4.4.0 luxon@3.7.2 \
  node-cron@4.6.0 node-schedule@2.1.1 cron-parser@4.9.0 cronosjs@1.7.1
cat > check.cjs <<'JS'
const FakeTimers = require('@sinonjs/fake-timers');
const [library, row] = process.argv.slice(2);
const expr = row === 'fixed' ? '30 1 * * *' : '*/30 * * * *';
const from = Date.parse('2026-10-24T21:00:00Z');
const to = Date.parse('2026-10-25T05:00:00Z');
const clock = FakeTimers.install({now: from - 1000,
  toFake: ['Date', 'setTimeout', 'clearTimeout', 'setInterval', 'clearInterval',
    'setImmediate', 'clearImmediate', 'performance', 'hrtime'], loopLimit: 100000});
const events = [];
const capture = () => events.push(new Date().toISOString());
let stop;
if (library === 'cron') {
  const job = new (require('cron').CronJob)(expr, capture, null, true, 'Europe/London');
  stop = () => job.stop();
} else if (library === 'node-cron') {
  const job = require('node-cron').schedule(expr, capture, {timezone: 'Europe/London'});
  stop = () => job.destroy();
} else if (library === 'node-schedule') {
  const job = require('node-schedule').scheduleJob({rule: expr, tz: 'Europe/London'}, capture);
  stop = () => job.cancel();
} else if (library === 'cronosjs') {
  const job = require('cronosjs').scheduleTask(expr, capture, {timezone: 'Europe/London'});
  stop = () => job.stop();
} else { clock.uninstall(); throw new Error('Unknown library'); }
(async () => {
  try {
    while (clock.now < to - 1) await clock.tickAsync(Math.min(60000, to - 1 - clock.now));
    const foldedUTC = events.filter(t => t >= '2026-10-25T00:00:00.000Z' && t < '2026-10-25T02:00:00.000Z');
    console.log(JSON.stringify({library, row, count: events.length, foldedUTC}));
  } finally {
    await stop();
    const remaining = clock.countTimers();
    clock.uninstall();
    if (remaining) throw new Error('Timers remain after stop');
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
JS
for library in cron node-cron node-schedule cronosjs; do
  TZ=UTC node check.cjs "$library" fixed
  TZ=UTC node check.cjs "$library" half-hour
done
```

The window is 24 October 21:00Z through 25 October 05:00Z, start-inclusive and end-exclusive. `count` covers that entire window. `foldedUTC` shows callbacks in the two occurrences of London's 01:00 hour: 00:00–00:59Z and 01:00–01:59Z.

Recorded output:

```jsonl
{"library":"cron","row":"fixed","count":1,"foldedUTC":["2026-10-25T00:30:00.000Z"]}
{"library":"cron","row":"half-hour","count":16,"foldedUTC":["2026-10-25T00:00:00.000Z","2026-10-25T00:30:00.000Z","2026-10-25T01:00:00.000Z","2026-10-25T01:30:00.000Z"]}
{"library":"node-cron","row":"fixed","count":1,"foldedUTC":["2026-10-25T01:30:00.000Z"]}
{"library":"node-cron","row":"half-hour","count":14,"foldedUTC":["2026-10-25T01:00:00.000Z","2026-10-25T01:30:00.000Z"]}
{"library":"node-schedule","row":"fixed","count":1,"foldedUTC":["2026-10-25T00:30:00.000Z"]}
{"library":"node-schedule","row":"half-hour","count":16,"foldedUTC":["2026-10-25T00:00:00.000Z","2026-10-25T00:30:00.000Z","2026-10-25T01:00:00.000Z","2026-10-25T01:30:00.000Z"]}
{"library":"cronosjs","row":"fixed","count":1,"foldedUTC":["2026-10-25T00:30:00.000Z"]}
{"library":"cronosjs","row":"half-hour","count":14,"foldedUTC":["2026-10-25T00:00:00.000Z","2026-10-25T00:30:00.000Z"]}
```

## What to change before the transition

This is general advice, not tested per application:

- Move a daily job outside the repeated hour and test the new time. Moving it just into the following hour is insufficient for the measured `cron@4.4.0` post-fold cases above.
- Use a UTC schedule if a fixed UTC time fits the business requirement. Its local business time can shift when the local offset changes.
- For work that must happen once, use a durable, atomic idempotency guard keyed to the intended business event or period before performing the side effect. For a half-hourly job, decide whether the two occurrences are distinct events before choosing the key.

An idempotency guard prevents a repeated side effect; it does not recover a missed run, enforce the configured local time or fix a scheduler's timer loop. Test the exact release, expression, timezone, startup time and handler that you deploy.

## Evidence and limits

The main comparison used actual registered callbacks under fake Date/timers, installed before importing each library, with a separate process per row and trivial handlers. Most London and New York windows cover four elapsed hours on either side of the fold; the Berlin daily window covers 24 October 20:00Z through 25 October 06:00Z. Croner's fixed and half-hourly rows were measured separately with native Date/libuv timers and a controlled libc clock. Native scheduled UTC targets repeated across reruns; raw delivery milliseconds retained operating-system jitter.

These checks cover the expressions, versions and windows above. They do not test live DST-night operation, application load, downtime, restart catch-up, persistence or distributed execution.

[NestJS #2389](https://github.com/nestjs/schedule/issues/2389) is **our own reproduction report**, not an independent user report. This comparison reran the pinned `cron` backend, not a new Nest application wrapper. [Cron #1087](https://github.com/kelektiv/node-cron/issues/1087) concerns preview dates returned before their input; preview output alone does not establish callback behavior.

Related: [n8n 2.40.7 at the 2026 fall-back](https://github.com/CyberNative-AI/.github/tree/main/notes/n8n-dst-2026).

Prepared with AI assistance. Published by CyberNative AI LLC. Corrections: hello@cybernative.ai.
