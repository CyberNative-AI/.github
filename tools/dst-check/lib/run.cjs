'use strict';
const {spawnSync} = require('node:child_process');
const path = require('node:path');
const {parts, stamp} = require('./time.cjs');
const {parse, calendarPolicy} = require('./expression.cjs');
const {supported, packageInfo} = require('./project.cjs');
const worker = path.join(__dirname, 'worker.cjs');
function execute(request) {
  const child = spawnSync(process.execPath, [worker], {
    cwd: request.projectDir,
    input: JSON.stringify(request),
    encoding: 'utf8',
    timeout: 30000,
    maxBuffer: 4 * 1024 * 1024,
    env: {PATH: process.env.PATH || '/usr/bin:/bin', TZ: 'UTC', LANG: 'C.UTF-8'}
  });
  if (child.error || !child.stdout.trim()) throw new Error('Controlled-time worker unavailable: ' + (child.error || child.stderr || 'no output'));
  let run;
  try { run = JSON.parse(child.stdout); }
  catch (_) { throw new Error('Controlled-time worker returned invalid JSON: ' + child.stdout.slice(0, 300)); }
  if (child.status !== 0 || run.status !== 'OK') throw new Error('Controlled-time run failed: ' + (run.error || child.stderr || run.status));
  if (child.stderr.trim()) throw new Error('Unexpected library stderr: ' + child.stderr);
  return run;
}
function reference(c) {
  const matcher = parse(c.expr), firstWall = new Set(), first = [], all = [];
  const start = Date.parse(c.from), end = Date.parse(c.to);
  for (let ms = Math.ceil(start / 60000) * 60000; ms < end; ms += 60000) {
    const p = parts(ms, c.tz);
    if (!matcher.matches(p)) continue;
    const utc = new Date(ms).toISOString();
    all.push(utc);
    if (!firstWall.has(p.wall)) { first.push(utc); firstWall.add(p.wall); }
  }
  const nonexistent = [];
  if (c.transition && c.transition.deltaMinutes > 0) {
    const at = Date.parse(c.transition.at);
    const localBegin = at + c.transition.beforeOffsetMinutes * 60000;
    for (let ms = localBegin; ms < localBegin + c.transition.deltaMinutes * 60000; ms += 60000) {
      const p = parts(ms, 'UTC');
      if (matcher.matches(p)) nonexistent.push(p.wall);
    }
  }
  return {policy: 'skip nonexistent wall slots; use the first occurrence of a repeated wall time', first, all, nonexistent};
}
function analyze(c, run) {
  const matcher = parse(c.expr);
  const expected = reference(c), wallCounts = new Map(), instantCounts = new Map();
  const events = run.events.map(event => {
    const ms = Date.parse(event.observedUTC), p = parts(ms, c.tz);
    wallCounts.set(p.wall, (wallCounts.get(p.wall) || 0) + 1);
    instantCounts.set(event.observedUTC, (instantCounts.get(event.observedUTC) || 0) + 1);
    return {...event, ...stamp(ms, c.tz), matchesExpression: parse(c.expr).matches(p)};
  });
  const observed = events.map(event => event.observedUTC), observedSet = new Set(observed);
  const repeatedWallTimes = [...wallCounts.entries()].filter(([, count]) => count > 1).map(([wall, count]) => ({wall, count}));
  const duplicateInstants = [...instantCounts.entries()].filter(([, count]) => count > 1).map(([utc, count]) => ({utc, count}));
  const flags = {
    gapSlots: expected.nonexistent.length,
    missingFirstSlots: expected.first.filter(utc => !observedSet.has(utc)),
    repeatedWallTimes,
    duplicateInstants,
    outOfExpression: events.filter(event => !event.matchesExpression).map(event => event.observedUTC),
    referenceDifference: JSON.stringify(observed) !== JSON.stringify(expected.first)
  };
  const repeated = new Set(repeatedWallTimes.map(entry => entry.wall));
  const duplicate = new Set(duplicateInstants.map(entry => entry.utc));
  const rows = events.map(event => {
    let label = 'ok';
    if (!event.matchesExpression) label = 'SHIFTED';
    else if (repeated.has(event.local.slice(0, 19)) || duplicate.has(event.observedUTC)) label = 'DUPLICATED';
    return {utc: event.utc, local: event.local, label, scheduledUTC: event.scheduledUTC, observedUTC: event.observedUTC};
  });
  const library = c.library || run.request.library;
  const version = c.version || (c.projectDir ? packageInfo(library, c.projectDir).version : undefined);
  function calendarReason(p) {
    if (library !== 'node-cron' || !matcher.matches(p) || matcher.matchesAnd(p)) return {};
    const proof = version === '4.6.0'
      ? 'This calendar-policy difference was demonstrated with node-cron@4.6.0.'
      : 'The observed absence is consistent with the documented node-cron AND rule; this installed version’s matcher was not independently verified.';
    return {reasonCode: 'CALENDAR_POLICY_DIFFERENCE', reason: 'This slot belongs only to the OR calendar reference; an AND calendar does not schedule it. ' + proof};
  }
  for (const utc of flags.missingFirstSlots) {
    rows.push({...stamp(Date.parse(utc), c.tz), label: 'MISSED', reason: 'Expected first-occurrence slot had no callback', ...calendarReason(parts(Date.parse(utc), c.tz))});
  }
  for (const local of expected.nonexistent) {
    rows.push({utc: null, local, label: 'MISSED', reason: 'This scheduled local wall time did not exist', ...calendarReason(parts(Date.parse(local + 'Z'), 'UTC'))});
  }
  rows.sort((a, b) => (a.utc || '').localeCompare(b.utc || '') || a.local.localeCompare(b.local) || a.label.localeCompare(b.label));
  return {events, reference: expected, calendarPolicy, flags, rows};
}
module.exports = {supported, packageInfo, execute, reference, analyze};
