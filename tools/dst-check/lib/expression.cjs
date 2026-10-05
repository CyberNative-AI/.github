'use strict';
// Independent, bounded classic-cron matcher. It does not use any tested scheduler.
function field(text, min, max, sunday = false) {
  const values = new Set();
  if (!/^[\d*,/\-]+$/.test(text)) throw new Error('Supported syntax: numeric *, lists, ranges and steps only');
  for (const item of text.split(',')) {
    const [base, stepText, extra] = item.split('/');
    const step = stepText === undefined ? 1 : Number(stepText);
    if (extra !== undefined || !Number.isInteger(step) || step < 1 || step > max - min + 1) throw new Error('Invalid step');
    let from, to;
    if (base === '*') [from, to] = [min, max];
    else if (/^\d+-\d+$/.test(base)) [from, to] = base.split('-').map(Number);
    else if (/^\d+$/.test(base)) { from = Number(base); to = stepText === undefined ? from : max; }
    else throw new Error('Invalid numeric field');
    if (from < min || to > max || from > to) throw new Error('Field out of range');
    for (let n = from; n <= to; n += step) values.add(sunday && n === 7 ? 0 : n);
  }
  return values;
}
const calendarPolicy = 'Day fields * and wildcard bases with numeric step 1 (including */1 and */01) are unrestricted. If one day field is unrestricted, require the other; if both are unrestricted, accept every day. If both are restricted, use day-of-month OR day-of-week. Full-domain ranges, lists and steps other than 1 remain restricted.';
function unrestricted(text) { return text === '*' || /^\*\/\d+$/.test(text) && Number(text.slice(2)) === 1; }
function parse(expr) {
  let fields = expr.trim().split(/\s+/);
  if (fields.length === 6) {
    if (fields[0] !== '0') throw new Error('Six-field expressions must use literal second 0; maximum frequency is once per minute');
    fields = fields.slice(1);
  }
  if (fields.length !== 5) throw new Error('Use a five-field expression, or six fields with second 0');
  const sets = fields.map((f, i) => field(f, [0, 0, 1, 1, 0][i], [59, 23, 31, 12, 7][i], i === 4));
  function matches(p) {
    const [minute, hour, dom, month, dow] = sets;
    const dayMatch = unrestricted(fields[2]) ? dow.has(p.weekday) : unrestricted(fields[4]) ? dom.has(p.day) : dom.has(p.day) || dow.has(p.weekday);
    return p.second === 0 && minute.has(p.minute) && hour.has(p.hour) && month.has(p.month) && dayMatch;
  }
  function matchesAnd(p) {
    return matches(p) && sets[2].has(p.day) && sets[4].has(p.weekday);
  }
  return {expr, matches, matchesAnd};
}
module.exports = {parse, calendarPolicy};
