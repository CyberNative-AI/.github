#!/usr/bin/env node
'use strict';
const path = require('node:path');
const {transitions} = require('../lib/time.cjs');
const {parse, calendarPolicy} = require('../lib/expression.cjs');
const {supported, packageInfo, execute, analyze} = require('../lib/run.cjs');
const methodLimits = 'This checker uses controlled fake time, not native timers. Millisecond-sensitive library paths can behave differently in production. Results are evidence for the exact expression, timezone and installed version under this method, not a guarantee of native-timer or production behavior.';
function parseArgs(args) {
  if (args.length < 2) throw new Error('Usage: dst-check "<cron expression>" <IANA zone> --library <cron|node-cron|node-schedule> [--project DIR] [--version X.Y.Z] [--year YYYY] [--before-hours N] [--after-hours N] [--json]');
  const options = {expression: args[0], zone: args[1], projectDir: process.cwd(), beforeHours: 4, afterHours: 4, json: false};
  parse(options.expression);
  for (let index = 2; index < args.length; index++) {
    const option = args[index];
    if (option === '--json') options.json = true;
    else if (option === '--library' || option === '--project' || option === '--version' || option === '--year' || option === '--before-hours' || option === '--after-hours') {
      const value = args[++index];
      if (!value) throw new Error('Missing value after ' + option);
      if (option === '--library') options.library = value;
      else if (option === '--project') options.projectDir = path.resolve(value);
      else if (option === '--version') options.expectedVersion = value;
      else if (option === '--year') options.year = Number(value);
      else if (option === '--before-hours') options.beforeHours = Number(value);
      else if (option === '--after-hours') options.afterHours = Number(value);
    } else throw new Error('Unknown option: ' + option);
  }
  if (!options.library) throw new Error('Choose the installed library with --library.');
  if (!supported.includes(options.library)) throw new Error('This version supports: ' + supported.join(', ') + '. Croner and cronosjs are not supported in this version.');
  if (options.year !== undefined && (!Number.isInteger(options.year) || options.year < 1970 || options.year > 2099)) throw new Error('Year must be from 1970 to 2099.');
  if (![options.beforeHours, options.afterHours].every(value => Number.isInteger(value) && value >= 0 && value <= 24) || options.beforeHours + options.afterHours < 1) throw new Error('Transition window hours must be whole numbers from 0 to 24, with a non-empty total window.');
  return options;
}
function dstConsequences(results) {
  const rows = results.flatMap(result => result.rows || []);
  if (!results.length) return {
    consequence: 'This timezone has no offset transition in the selected range, so this run found no DST boundary for the schedule.',
    hint: 'Choose a fixed UTC cadence only if changing local fire times across offset changes and regions is acceptable. If fixed local wall time is required, use the intended IANA timezone and re-test the exact expression, timezone and installed library version. UTC is not a universal fix for library defects.'
  };
  if (rows.some(row => row.label === 'SHIFTED')) return {
    consequence: 'At least one callback ran at a local time that does not match the expression.',
    hint: 'Moving outside the clock-change window is not sufficient: Berlin cron@4.4.0 with 0 3 * * * fired at 02:00 and 03:00 in this controlled-time check. Re-test the exact expression, timezone and installed library version after any configuration change. Choose a fixed UTC cadence only if changing local fire times across offset changes and regions is acceptable. If fixed local wall time is required, use the intended IANA timezone and re-test the exact expression, timezone and installed library version. UTC is not a universal fix for library defects.'
  };
  if (rows.some(row => row.label === 'DUPLICATED')) return {
    consequence: 'A repeated local wall time produced more than one callback.',
    hint: 'Use UTC or make the handler idempotent before the repeated hour.'
  };
  if (rows.some(row => row.label === 'MISSED')) {
    const gapSlotMissing = results.some(result => result.transition.kind === 'gap' && result.rows.some(row => row.label === 'MISSED' && row.utc === null));
    if (gapSlotMissing) return {
      consequence: 'At least one scheduled local time did not exist during the spring clock jump.',
      hint: 'Use UTC or move this job outside the skipped local hour; decide whether that run must happen another way.'
    };
    return {
      consequence: 'At least one expected schedule occurrence had no callback under the selected comparison policy.',
      hint: 'Use UTC or define how the job should handle a missing occurrence during the repeated hour.'
    };
  }
  return {
    consequence: 'Every observed callback matched the selected first-occurrence comparison policy in these windows.',
    hint: 'Choose a fixed UTC cadence only if changing local fire times across offset changes and regions is acceptable. If fixed local wall time is required, use the intended IANA timezone and re-test the exact expression, timezone and installed library version. UTC is not a universal fix for library defects.'
  };
}
function consequences(results) {
  const policyRows = results.flatMap(result => result.rows || []).filter(row => row.reasonCode === 'CALENDAR_POLICY_DIFFERENCE');
  if (!policyRows.length) return dstConsequences(results);
  const filtered = results.map(result => ({...result, rows: (result.rows || []).filter(row => row.reasonCode !== 'CALENDAR_POLICY_DIFFERENCE')}));
  const advice = 'Confirm the intended day rule and re-test the exact expression, timezone and installed library version.';
  const disclosure = 'Reference-only slots belong to the OR calendar baseline; an AND calendar does not schedule them. This is a calendar-policy comparison, not a DST-defect verdict.';
  if (!filtered.some(result => result.rows.some(row => row.label !== 'ok'))) return {consequence: disclosure, hint: advice};
  const guidance = dstConsequences(filtered);
  return {consequence: guidance.consequence + ' Separately: ' + disclosure, hint: guidance.hint + ' Calendar policy: ' + advice};
}
function main() {
  if (Number(process.versions.node.split('.')[0]) < 20) throw new Error('Node.js 20 or newer is required.');
  const options = parseArgs(process.argv.slice(2));
  const projectDir = path.resolve(options.projectDir);
  const installed = packageInfo(options.library, projectDir);
  if (options.expectedVersion && installed.version !== options.expectedVersion) throw new Error('Installed ' + options.library + ' version is ' + installed.version + ', not requested ' + options.expectedVersion + '.');
  const now = Date.now(), currentYear = new Date(now).getUTCFullYear();
  const years = options.year === undefined ? [currentYear, currentYear + 1] : [options.year];
  let found = years.flatMap(year => transitions(options.zone, year));
  if (options.year === undefined) found = found.filter(item => Date.parse(item.at) > now).slice(0, 2);
  const results = found.map(transition => {
    const at = Date.parse(transition.at);
    const request = {library: options.library, expr: options.expression, tz: options.zone,
      from: new Date(at - options.beforeHours * 3600000).toISOString(), to: new Date(at + options.afterHours * 3600000).toISOString(),
      projectDir, ...(options.expectedVersion ? {expectedVersion: options.expectedVersion} : {})};
    const run = execute(request), analysis = analyze({id: transition.kind, library: installed.name, version: installed.version, expr: options.expression, tz: options.zone, from: request.from, to: request.to, transition}, run);
    return {transition, events: analysis.events, rows: analysis.rows, flags: analysis.flags, run};
  });
  const guidance = consequences(results);
  const report = {expression: options.expression, zone: options.zone, library: installed.name, version: installed.version,
    calendarPolicy, methodLimits,
    comparisonPolicy: 'Skip nonexistent wall slots and use the first occurrence of a repeated wall time. This is a comparison policy, not a universal DST rule.',
    window: options.beforeHours + ' elapsed hour(s) before through ' + options.afterHours + ' after each transition; end is exclusive.',
    runtime: {node: process.version, icu: process.versions.icu, tz: process.versions.tz}, results, ...guidance};
  if (options.json) process.stdout.write(JSON.stringify(report, null, 2) + '\n');
  else {
    console.log('DST check: ' + options.expression + ' | ' + options.zone + ' | ' + installed.name + '@' + installed.version);
    console.log('Controlled-time callbacks; times show UTC and local offset. ' + report.window);
    console.log(report.comparisonPolicy);
    console.log(report.calendarPolicy);
    if (!results.length) console.log('No offset transition found in the selected range.');
    for (const result of results) {
      console.log('\n' + result.transition.kind.toUpperCase() + ' ' + result.transition.at + ' (' + result.transition.deltaMinutes + ' minutes)');
      for (const row of result.rows) console.log('  ' + row.label.padEnd(11) + (row.utc || 'no UTC instant') + ' | ' + row.local + (row.reason ? ' | ' + row.reason : ''));
    }
    console.log('\nConsequence: ' + report.consequence);
    console.log('Safer hint: ' + report.hint);
    console.log('Limits: ' + methodLimits + ' this is a controlled-time check, not a production run. See README for tested versions and coverage.');
  }
}
if (require.main === module) {
  try { main(); }
  catch (err) { console.error(err.message); process.exitCode = 1; }
}
module.exports = {consequences};
