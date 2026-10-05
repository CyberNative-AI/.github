'use strict';
const fs = require('node:fs');
const path = require('node:path');
const FakeTimers = require('../vendor/node_modules/@sinonjs/fake-timers');
const {projectRequire, packageInfo} = require('./project.cjs');
const request = JSON.parse(fs.readFileSync(0, 'utf8'));
const start = Date.parse(request.from), end = Date.parse(request.to);
if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start || end - start > 48 * 3600000) throw new Error('Invalid or oversized transition window');
const runtime = {node: process.version, icu: process.versions.icu, tz: process.versions.tz, defaultZone: Intl.DateTimeFormat().resolvedOptions().timeZone};
let clock, stop = () => {}, status = 'OK', error, steps = 0;
const events = [], errors = [];
const safeRequest = {...request};
delete safeRequest.projectDir;
function capture(scheduled) {
  if (events.length >= 5000) throw new Error('Callback limit exceeded');
  const observedUTC = new Date().toISOString();
  events.push({scheduledUTC: scheduled ? new Date(scheduled).toISOString() : observedUTC, observedUTC});
}
async function main() {
  try {
    if (Number(process.versions.node.split('.')[0]) < 20) throw new Error('Node.js 20 or newer is required');
    const info = packageInfo(request.library, request.projectDir);
    if (request.expectedVersion && info.version !== request.expectedVersion) {
      throw new Error('Installed ' + request.library + ' version is ' + info.version + ', not requested ' + request.expectedVersion);
    }
    const req = projectRequire(request.projectDir);
    clock = FakeTimers.install({now: start - 1000,
      toFake: ['Date', 'setTimeout', 'clearTimeout', 'setInterval', 'clearInterval', 'setImmediate', 'clearImmediate', 'performance', 'hrtime'],
      loopLimit: 100000});
    if (request.library === 'cron') {
      const {CronJob} = req('cron');
      const job = new CronJob(request.expr, () => capture(), null, true, request.tz);
      stop = () => job.stop();
    } else if (request.library === 'node-cron') {
      const cron = req('node-cron');
      const job = cron.schedule(request.expr, context => capture(context && context.date),
        {timezone: request.tz, noOverlap: false, maxRandomDelay: 0, distributed: false});
      for (const name of ['execution:failed', 'execution:missed', 'execution:overlap']) {
        if (typeof job.on === 'function') job.on(name, context => errors.push({name, at: context.date.toISOString()}));
      }
      stop = () => { if (typeof job.destroy === 'function') job.destroy(); else if (typeof job.stop === 'function') job.stop(); };
    } else if (request.library === 'node-schedule') {
      const schedule = req('node-schedule');
      const job = schedule.scheduleJob({rule: request.expr, tz: request.tz}, date => capture(date));
      if (!job) throw new Error('Schedule registration was rejected');
      if (typeof job.on === 'function') job.on('error', err => errors.push(String(err)));
      stop = () => job.cancel();
    } else {
      throw new Error('Supported libraries in this partial build: cron, node-cron, node-schedule');
    }
    while (clock.now < end - 1) {
      await clock.tickAsync(Math.min(request.advanceMS || 60000, end - 1 - clock.now));
      if (++steps > 200000) throw new Error('Controlled clock step limit exceeded');
    }
    if (errors.length) throw new Error('The selected library reported an execution error: ' + JSON.stringify(errors));
    if (events.some(event => Date.parse(event.observedUTC) < start || Date.parse(event.observedUTC) >= end)) throw new Error('A callback fell outside the requested window');
  } catch (err) { status = 'ERROR'; error = String(err.stack || err); }
  finally {
    try { await stop(); } catch (err) { status = 'ERROR'; error = String(err.stack || err); }
    const remainingTimers = clock ? clock.countTimers() : 0;
    if (clock) clock.uninstall();
    if (remainingTimers) { status = 'ERROR'; error = (error || '') + '; timers remain after cleanup: ' + remainingTimers; }
    process.stdout.write(JSON.stringify({status, ...(error ? {error} : {}), request: safeRequest, runtime, events, errors, clockSteps: steps,
      cleanup: {remainingTimers, clockRestored: Boolean(clock)}}) + '\n');
    if (status !== 'OK') process.exitCode = 1;
  }
}
main().catch(err => { process.stderr.write(String(err)); process.exitCode = 1; });
