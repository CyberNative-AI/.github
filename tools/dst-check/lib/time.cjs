'use strict';
const formatters = new Map();
function parts(ms, tz) {
  if (!formatters.has(tz)) formatters.set(tz, new Intl.DateTimeFormat('en-GB', {
    timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23'
  }));
  const p = Object.fromEntries(formatters.get(tz).formatToParts(new Date(ms))
    .filter(p => p.type !== 'literal').map(p => [p.type, Number(p.value)]));
  p.wallMS = Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second);
  p.offsetMinutes = (p.wallMS - Math.floor(ms / 1000) * 1000) / 60000;
  p.weekday = new Date(p.wallMS).getUTCDay();
  p.wall = new Date(p.wallMS).toISOString().slice(0, 19);
  return p;
}
function stamp(ms, tz) {
  const p = parts(ms, tz), sign = p.offsetMinutes < 0 ? '-' : '+';
  const offset = Math.abs(p.offsetMinutes);
  return {utc: new Date(ms).toISOString(), local: p.wall + sign +
    String(Math.floor(offset / 60)).padStart(2, '0') + ':' + String(offset % 60).padStart(2, '0')};
}
function transitions(tz, year) {
  parts(Date.UTC(year, 0, 1), tz); // validate zone even if no transition
  const result = [], begin = Date.UTC(year, 0, 1), end = Date.UTC(year + 1, 0, 1);
  let previous = parts(begin, tz).offsetMinutes;
  for (let ms = begin + 6 * 3600000; ms <= end; ms += 6 * 3600000) {
    const offset = parts(ms, tz).offsetMinutes;
    if (offset !== previous) {
      let lo = ms - 6 * 3600000, hi = ms;
      while (hi - lo > 60000) {
        const middle = Math.floor((lo + hi) / 120000) * 60000;
        if (parts(middle, tz).offsetMinutes === previous) lo = middle; else hi = middle;
      }
      result.push({at: new Date(hi).toISOString(), kind: offset > previous ? 'gap' : 'overlap',
        beforeOffsetMinutes: previous, afterOffsetMinutes: offset,
        deltaMinutes: offset - previous, before: stamp(hi - 1000, tz), after: stamp(hi, tz)});
      previous = offset;
    }
  }
  return result;
}
module.exports = {parts, stamp, transitions};
