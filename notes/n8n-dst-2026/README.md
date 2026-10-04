

**n8n 2.40.7 DST heads-up: extra daily runs in Berlin and New York in simulated-clock tests**

Tested on 4 October 2026. In a simulated-clock test of n8n 2.40.7, a daily `0 3 * * *` Schedule Trigger in Europe/Berlin fired twice on Sunday 25 October 2026. The extra run came one hour early, at 02:00 CET (01:00 UTC). A daily `30 2 * * *` trigger in America/New_York fired twice on Sunday 1 November, with an extra run at 01:30 EST (06:30 UTC), one hour before the configured 02:30 time.

Direct calculations with the same `cron` 4.4.0 scheduler also produce an extra occurrence for every minute from 03:00 to 03:59 in Berlin and 02:00 to 02:59 in New York on those dates. These are calculations, not callback tests of every minute or a live server through a real clock change. Choosing a time after the repeated hour did not prevent the extra callback in the two tested schedules above.

Calculated times (`cron` 4.4.0, Luxon 3.7.2):

| Daily schedule (timezone) | Date | Calculated runs that local day | Extra occurrence at |
|---|---|---|---|
| `0 3 * * *` (Europe/Berlin) | 25 Oct 2026 | 2 | 02:00 CET (01:00 UTC) |
| `30 3 * * *` / `59 3 * * *` (Europe/Berlin) | 25 Oct 2026 | 2 | 02:30 / 02:59 CET |
| `0 2 * * *` / `30 2 * * *` / `59 2 * * *` (Europe/Berlin) | 25 Oct 2026 | 1 | — |
| `0 4 * * *` (Europe/Berlin) | 25 Oct 2026 | 1 | — |
| `0 2 * * *` / `30 2 * * *` / `59 2 * * *` (America/New_York) | 1 Nov 2026 | 2 | 01:00 / 01:30 / 01:59 EST |
| `0 1 * * *` / `30 1 * * *` / `0 3 * * *` / `0 4 * * *` (America/New_York) | 1 Nov 2026 | 1 | — |

How we tested: we ran n8n's Schedule Trigger node and scheduling-manager code from the published packages, unchanged, in a local harness with a simulated clock. We recorded each callback across the transition windows and repeated the tests with identical results. The two duplicate-run callback ledgers match the calculated times above. In the same harness, `30 2 * * *` in Berlin and `30 1 * * *` and `0 3 * * *` in New York fired once on their respective transition dates. Matched controls using the same expressions one week earlier and in UTC fired once per day.

The Schedule Trigger's one-day “Days” mode builds a daily six-field cron expression. Calculating `0 0 3 * * *` and `0 30 3 * * *` in Berlin also gives an extra time that night, but we did not execute Days-mode triggers. Our callback tests used Custom (Cron) expressions. We tested only Europe/Berlin and America/New_York, did not run a live n8n server through a real transition, and did not test n8n 1.x or other n8n 2.x versions.

The standalone `cron` calls below reproduce the calculation without n8n. They do not verify other applications' callback behavior. The related upstream [report #1087](https://github.com/kelektiv/node-cron/issues/1087) and [proposed fix #1088](https://github.com/kelektiv/node-cron/pull/1088) concern returning a date before the input time; the examples here return an extra future occurrence.

You can check the computed times yourself (Node.js, `npm install --ignore-scripts cron@4.4.0 luxon@3.7.2`):

```js
const { CronTime } = require('cron');
const { DateTime } = require('luxon');
function runs(expr, zone, fromUtc, toUtc) {
  const t = new CronTime(expr, zone);
  let d = DateTime.fromISO(fromUtc, { zone });
  const end = DateTime.fromISO(toUtc).toMillis();
  const out = [];
  for (;;) {
    d = t.getNextDateFrom(d);
    if (d.toMillis() >= end) return out;
    out.push(`${d.toUTC().toISO()}  (${d.toISO()})`);
  }
}
console.log(runs('0 3 * * *', 'Europe/Berlin', '2026-10-24T12:00:00Z', '2026-10-26T12:00:00Z'));
console.log(runs('30 2 * * *', 'America/New_York', '2026-10-31T12:00:00Z', '2026-11-02T12:00:00Z'));
```

It prints three timestamps for each schedule: the extra occurrence first, the configured time on the transition date, and the configured time on the following day.

Before the relevant transition (25 October in Berlin; 1 November in New York):

- Check daily workflows scheduled in the affected hour above, and test the exact version and configuration you use.
- Consider a temporary daily time such as 04:00 in the same timezone; it calculated once on each transition date in our checks. Or use UTC and adjust the hour for the intended business time. UTC has no daylight-saving clock change.
- For workflows where duplicates could cause harm, use a durable, atomic once-per-business-day guard before sending emails, creating invoices, publishing posts or making charges. This is general advice, not a tested n8n workflow.

These results cover only the versions, inputs, timezones and dates stated here. They do not establish the behavior of every n8n setup.

— CyberNative AI LLC

Prepared with AI assistance. Corrections: hello@cybernative.ai. We will publish dated corrections if these results need to change.

