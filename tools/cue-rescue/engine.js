/* Cue Rescue: dependency-free deterministic planning engine. */
(function (root) {
  'use strict';
  const LIMITS = Object.freeze({ cues: 12, rooms: 4, resources: 8, horizon: 720 });
  const record = x => x !== null && typeof x === 'object' && !Array.isArray(x) &&
    (Object.getPrototypeOf(x) === Object.prototype || Object.getPrototypeOf(x) === null);
  const integer = x => Number.isSafeInteger(x);
  const text = (x, n) => typeof x === 'string' && x.trim().length > 0 && x.length <= n;
  const clone = x => JSON.parse(JSON.stringify(x));
  const canonical = x => JSON.stringify(x, function (_, value) {
    if (!record(value)) return value;
    const sorted = Object.create(null);
    Object.keys(value).sort().forEach(k => { sorted[k] = value[k]; });
    return sorted;
  });
  const overlap = (a, b) => a.start < b.end && b.start < a.end;
  const cmp = (a, b) => a < b ? -1 : a > b ? 1 : 0;

  function validate(plan) {
    const errors = [];
    const fail = s => errors.push(s);
    if (!record(plan)) return { ok: false, errors: ['Plan must be a plain object.'] };
    if (plan.version !== 1) fail('Only plan version 1 is supported.');
    if (!text(plan.title, 256)) fail('Plan title must contain 1–256 characters.');
    const h = plan.horizon;
    const validHorizon = record(h) && integer(h.start) && integer(h.end) && h.start >= 0 &&
      h.end > h.start && h.end - h.start <= LIMITS.horizon;
    if (!validHorizon) fail('Horizon must be nonnegative integer minutes with span 1–720.');
    const ids = new Set();
    if (!Array.isArray(plan.resources) || plan.resources.length > LIMITS.resources) {
      fail('Plan must have at most 8 resources.');
    } else for (const r of plan.resources) {
      if (!record(r) || !text(r.id, 80) || !text(r.label, 256)) { fail('Each resource needs an id and label.'); continue; }
      if (ids.has(r.id)) fail('Duplicate resource id: ' + r.id);
      ids.add(r.id);
    }
    const cueIds = new Set(), rooms = new Set();
    if (!Array.isArray(plan.cues) || plan.cues.length < 1 || plan.cues.length > LIMITS.cues) {
      fail('Plan must have 1–12 cues.');
    } else for (const c of plan.cues) {
      if (!record(c)) { fail('Each cue must be a plain object.'); continue; }
      if (!text(c.id, 80) || !text(c.title, 256) || !text(c.room, 80)) fail('Each cue needs bounded id, title and room text.');
      if (cueIds.has(c.id)) fail('Duplicate cue id: ' + c.id);
      cueIds.add(c.id); rooms.add(c.room);
      if (!integer(c.duration) || c.duration <= 0 || c.duration > LIMITS.horizon ||
          !integer(c.minDuration) || c.minDuration <= 0 || c.minDuration > c.duration) fail('Cue ' + c.id + ': invalid duration/minimum.');
      for (const key of ['plannedStart', 'notBefore', 'deadline']) {
        if (!integer(c[key]) || (validHorizon && (c[key] < h.start || c[key] > h.end))) fail('Cue ' + c.id + ': invalid ' + key + '.');
      }
      if (typeof c.locked !== 'boolean') fail('Cue ' + c.id + ': locked must be boolean.');
      if (!integer(c.priority) || c.priority < 1 || c.priority > 3) fail('Cue ' + c.id + ': priority must be 1–3.');
      if (!Array.isArray(c.resources) || c.resources.length > LIMITS.resources) fail('Cue ' + c.id + ': invalid resources.');
      else {
        const seen = new Set();
        for (const id of c.resources) {
          if (typeof id !== 'string' || !ids.has(id)) fail('Cue ' + c.id + ': unknown resource.');
          if (seen.has(id)) fail('Cue ' + c.id + ': duplicate resource.');
          seen.add(id);
        }
      }
    }
    if (rooms.size > LIMITS.rooms) fail('Plan must have at most 4 rooms.');
    // Unknown fields are rejected: this prevents silent acceptance of unsupported models.
    function fields(o, allowed, label) {
      if (record(o) && Object.keys(o).some(k => !allowed.includes(k))) fail(label + ': unsupported field.');
    }
    fields(plan, ['version','title','horizon','resources','cues'], 'Plan');
    fields(h, ['start','end'], 'Horizon');
    if (Array.isArray(plan.resources)) plan.resources.forEach(r => fields(r, ['id','label'], 'Resource'));
    if (Array.isArray(plan.cues)) plan.cues.forEach(c => fields(c,
      ['id','title','room','plannedStart','duration','minDuration','locked','notBefore','deadline','resources','priority'], 'Cue'));
    return { ok: errors.length === 0, errors };
  }

  function validateScenario(plan, scenario) {
    const errors = [], cueIds = new Set(plan.cues.map(c => c.id)), resourceIds = new Set(plan.resources.map(r => r.id));
    if (!record(scenario)) return ['Scenario must be a plain object.'];
    if (Object.keys(scenario).some(k => !['delays','unavailable'].includes(k))) errors.push('Unsupported scenario field.');
    if (!Array.isArray(scenario.delays) || scenario.delays.length > 12) errors.push('Scenario needs at most 12 delays.');
    else {
      const seen = new Set();
      for (const d of scenario.delays) {
        if (!record(d) || Object.keys(d).some(k => !['cueId','minutes'].includes(k)) || !cueIds.has(d.cueId) ||
            !integer(d.minutes) || d.minutes < 0 || d.minutes > 720) errors.push('Invalid cue delay.');
        else if (seen.has(d.cueId)) errors.push('Duplicate cue delay.');
        if (record(d)) seen.add(d.cueId);
      }
    }
    if (!Array.isArray(scenario.unavailable) || scenario.unavailable.length > 32) errors.push('Scenario needs at most 32 unavailable intervals.');
    else for (const u of scenario.unavailable) {
      if (!record(u) || Object.keys(u).some(k => !['resourceId','start','end'].includes(k)) || !resourceIds.has(u.resourceId) ||
          !integer(u.start) || !integer(u.end) || u.start < plan.horizon.start || u.end > plan.horizon.end || u.end <= u.start) {
        errors.push('Invalid resource unavailable interval.');
      }
    }
    return errors;
  }

  function input(plan, scenario) {
    const p = validate(plan);
    if (!p.ok) return p.errors;
    return validateScenario(plan, scenario);
  }
  const emptyScenario = () => ({ delays: [], unavailable: [] });
  function lowerBound(c, scenario) {
    const d = scenario.delays.find(d => d.cueId === c.id);
    return Math.max(c.notBefore, d ? c.plannedStart + d.minutes : c.notBefore);
  }
  function row(c, start, duration) {
    return { cueId: c.id, id: c.id, title: c.title, room: c.room, start, end: start + duration,
      duration, resources: [...c.resources], plannedStart: c.plannedStart, minDuration: c.minDuration,
      locked: c.locked, priority: c.priority };
  }

  // Independent final validator: interval sweeps, not the search's placement check.
  function validateSchedule(plan, scenario, schedule) {
    const errors = input(plan, scenario);
    if (errors.length) return { ok: false, conflicts: errors.map(message => ({ type: 'invalid-input', cueIds: [], message })) };
    const conflicts = [], byId = new Map(plan.cues.map(c => [c.id, c])), seen = new Set();
    const add = (type, cueIds, message, extra) => conflicts.push({ type, cueIds, message, ...extra });
    if (!Array.isArray(schedule)) return { ok: false, conflicts: [{ type: 'invalid-schedule', cueIds: [], message: 'Schedule must be an array.' }] };
    const rooms = new Map(), resources = new Map();
    for (const s of schedule) {
      if (!record(s) || !byId.has(s.cueId) || seen.has(s.cueId)) { add('invalid-schedule', [], 'Unknown or duplicate schedule cue.'); continue; }
      seen.add(s.cueId);
      const c = byId.get(s.cueId);
      if (!integer(s.start) || !integer(s.duration) || s.duration < c.minDuration || s.duration > c.duration ||
          s.end !== s.start + s.duration || s.room !== c.room || !Array.isArray(s.resources) ||
          s.resources.length !== c.resources.length || ![...s.resources].sort().every((id,i) => id === [...c.resources].sort()[i]) ||
          s.id !== c.id || s.title !== c.title || s.plannedStart !== c.plannedStart || s.minDuration !== c.minDuration ||
          s.locked !== c.locked || s.priority !== c.priority || Object.keys(s).some(k =>
            !['cueId','id','title','room','start','end','duration','resources','plannedStart','minDuration','locked','priority'].includes(k))) {
        add('invalid-schedule', [c.id], c.title + ': altered or invalid schedule fields.'); continue;
      }
      if (c.locked && (s.start !== c.plannedStart || s.duration !== c.duration)) add('lock', [c.id], c.title + ': locked timing was changed.');
      if (s.start < Math.max(plan.horizon.start, lowerBound(c, scenario))) add('not-before', [c.id], c.title + ': starts before its required time.');
      if (s.end > Math.min(c.deadline, plan.horizon.end)) add('cutoff', [c.id], c.title + ': ends after its hard cutoff.');
      if (!rooms.has(c.room)) rooms.set(c.room, []);
      rooms.get(c.room).push(s);
      for (const id of c.resources) {
        if (!resources.has(id)) resources.set(id, []);
        resources.get(id).push(s);
      }
    }
    for (const c of plan.cues) if (!seen.has(c.id)) add('missing-cue', [c.id], c.title + ': cue is missing.');
    function sweep(items, type, key) {
      const sorted = [...items].sort((a,b) => a.start - b.start || cmp(a.cueId,b.cueId));
      for (let i = 0; i < sorted.length; i++) {
        for (let j = i + 1; j < sorted.length && sorted[j].start < sorted[i].end; j++) {
          const a = sorted[i], b = sorted[j];
          add(type, [a.cueId,b.cueId].sort(), (type === 'room' ? 'Room ' : 'Resource ') + key + ': ' + a.title + ' overlaps ' + b.title + '.',
            { [type === 'room' ? 'room' : 'resourceId']: key, start: Math.max(a.start,b.start), end: Math.min(a.end,b.end) });
        }
      }
    }
    for (const [key, items] of rooms) sweep(items, 'room', key);
    for (const [key, items] of resources) {
      sweep(items, 'resource', key);
      for (const s of items) for (const u of scenario.unavailable) {
        if (u.resourceId === key && overlap(s,u)) add('unavailable', [s.cueId], s.title + ': resource ' + key + ' is unavailable.',
          { resourceId: key, start: Math.max(s.start,u.start), end: Math.min(s.end,u.end) });
      }
    }
    return { ok: conflicts.length === 0, conflicts };
  }
  function summarize(plan, schedule, conflicts) {
    let totalLateness = 0, totalShortening = 0, cost = 0;
    const byId = new Map(plan.cues.map(c => [c.id,c]));
    for (const s of schedule) {
      const c = byId.get(s.cueId), late = Math.max(0,s.start-c.plannedStart), short = c.duration-s.duration;
      totalLateness += late; totalShortening += short; cost += c.priority * (late + 3 * short);
    }
    return { feasible: conflicts.length === 0, conflictCount: conflicts.length, totalLateness, totalShortening, cost };
  }
  function evaluate(plan, scenario = emptyScenario()) {
    const errors = input(plan, scenario);
    if (errors.length) return { schedule: [], conflicts: errors.map(message => ({ type: 'invalid-input', cueIds: [], message })),
      summary: { feasible: false, conflictCount: errors.length, totalLateness: 0, totalShortening: 0, cost: 0 } };
    const schedule = plan.cues.map(c => row(c,c.locked ? c.plannedStart : Math.max(c.plannedStart,lowerBound(c,scenario)),c.duration));
    const check = validateSchedule(plan,scenario,schedule);
    return { schedule, conflicts: check.conflicts, summary: summarize(plan,schedule,check.conflicts) };
  }

  function repair(plan, scenario = emptyScenario(), settings = {}) {
    if (!record(settings)) return { options: [], search: { examined: 0, exhaustive: false, stoppedBecause: 'invalid-input' }, noSolutionReason: 'Search settings must be a plain object.' };
    const errors = input(plan,scenario), budget = settings.maxCandidates === undefined ? 5000 : settings.maxCandidates,
      maxOptions = settings.maxOptions === undefined ? 3 : settings.maxOptions;
    if (errors.length || !integer(budget) || budget < 1 || budget > 100000 || !integer(maxOptions) || maxOptions < 1 || maxOptions > 10) {
      return { options: [], search: { examined: 0, exhaustive: false, stoppedBecause: 'invalid-input' },
        noSolutionReason: errors.join(' ') || 'Search budget must be 1–100000 and options 1–10.' };
    }
    const source = clone(plan), applied = clone(scenario), selected = [], options = [];
    let examined = 0, truncated = false;
    const cues = [...source.cues].sort((a,b) => Number(b.locked)-Number(a.locked) || lowerBound(a,applied)-lowerBound(b,applied) ||
      (a.deadline-lowerBound(a,applied)-a.minDuration)-(b.deadline-lowerBound(b,applied)-b.minDuration) || cmp(a.id,b.id));
    const key = schedule => schedule.map(s => [s.cueId,s.start,s.duration]);
    function offer() {
      const schedule = source.cues.map(c => selected.find(s => s.cueId === c.id));
      const summary = summarize(source,schedule,[]), signature = JSON.stringify(key(schedule)), id = 'recovery-' + signature;
      const worst = options[options.length-1];
      // Avoid cloning and validating losing schedules; every option actually returned still passes the independent validator.
      if (options.length === maxOptions && (summary.cost > worst.cost || (summary.cost === worst.cost && cmp(id,worst.id) >= 0))) return;
      const check = validateSchedule(source,applied,schedule);
      if (!check.ok) return; // Never offer a candidate solely because search accepted it.
      const option = { id, plan: clone(source), scenario: clone(applied), schedule: clone(schedule),
        conflicts: [], summary, cost: summary.cost,
        changes: schedule.filter(s => s.start !== s.plannedStart || s.duration !== source.cues.find(c => c.id === s.cueId).duration)
          .map(s => ({ cueId: s.cueId, fromStart: s.plannedStart, toStart: s.start,
            fromDuration: source.cues.find(c => c.id === s.cueId).duration, toDuration: s.duration })) };
      options.push(option);
      options.sort((a,b) => a.cost-b.cost || cmp(a.id,b.id));
      if (options.length > maxOptions) options.pop();
    }
    // Search uses pairwise placements; final validator above builds independent interval buckets.
    function fits(c, start, duration) {
      const end = start + duration;
      if (start < Math.max(source.horizon.start,lowerBound(c,applied)) || end > Math.min(c.deadline,source.horizon.end)) return false;
      for (const u of applied.unavailable) if (c.resources.includes(u.resourceId) && start < u.end && u.start < end) return false;
      for (const s of selected) if (start < s.end && s.start < end &&
        (c.room === s.room || c.resources.some(id => s.resources.includes(id)))) return false;
      return true;
    }
    function visit(depth) {
      if (depth === cues.length) { offer(); return; }
      const c = cues[depth], low = c.locked ? c.plannedStart : Math.max(source.horizon.start,lowerBound(c,applied)),
        min = c.locked ? c.duration : c.minDuration;
      // Preserve duration first; all permitted integer durations and starts are included.
      for (let duration = c.duration; duration >= min; duration--) {
        const high = c.locked ? c.plannedStart : Math.min(c.deadline,source.horizon.end)-duration;
        for (let start = low; start <= high; start++) {
          if (examined >= budget) { truncated = true; return; }
          examined++;
          if (!fits(c,start,duration)) continue;
          selected.push(row(c,start,duration)); visit(depth+1); selected.pop();
          if (truncated) return;
        }
      }
    }
    visit(0);
    return { options, search: { examined, exhaustive: !truncated, stoppedBecause: truncated ? 'candidate-budget' : 'complete' },
      noSolutionReason: options.length ? null : truncated ? 'No feasible repair found within the candidate budget. Infeasibility is not established.' :
        'No schedule can retain every cue under these integer-minute constraints.' };
  }

  function exportPlan(option) {
    if (!record(option)) throw new TypeError('A validated recovery option is required.');
    const check = validateSchedule(option.plan,option.scenario,option.schedule);
    if (!check.ok) throw new TypeError('Recovery option is invalid.');
    const plan = clone(option.plan);
    for (const c of plan.cues) {
      const s = option.schedule.find(s => s.cueId === c.id);
      c.notBefore = lowerBound(c,option.scenario);
      c.plannedStart = s.start; c.duration = s.duration;
    }
    const valid = validate(plan);
    if (!valid.ok) throw new TypeError(valid.errors.join(' '));
    return { format: 'cue-rescue-recovery', version: 1, plan,
      scenario: { delays: [], unavailable: clone(option.scenario.unavailable) },
      provenance: { delayMode: 'materialized-in-plan', plan: clone(option.plan), scenario: clone(option.scenario) },
      schedule: clone(option.schedule), changes: clone(option.changes || []), summary: summarize(option.plan,option.schedule,[]) };
  }
  function readInput(data) {
    const invalid = errors => ({ ok: false, errors, plan: null, scenario: null, accepted: null });
    if (!record(data) || data.format === undefined) {
      const valid = validate(data);
      return valid.ok ? { ok: true, errors: [], plan: clone(data), scenario: emptyScenario(), accepted: null } : invalid(valid.errors);
    }
    if (data.format !== 'cue-rescue-recovery' || data.version !== 1 ||
        Object.keys(data).some(k => !['format','version','plan','scenario','provenance','schedule','changes','summary'].includes(k)) ||
        !record(data.provenance) || data.provenance.delayMode !== 'materialized-in-plan' ||
        Object.keys(data.provenance).some(k => !['delayMode','plan','scenario'].includes(k))) return invalid(['Unsupported recovery envelope.']);
    const original = data.provenance.plan, applied = data.provenance.scenario;
    const errors = [...input(original,applied), ...input(data.plan,data.scenario)];
    if (errors.length) return invalid(errors);
    if (data.scenario.delays.length !== 0 || canonical(data.scenario.unavailable) !== canonical(applied.unavailable)) return invalid(['Replay must retain unavailable intervals and materialize delays once.']);
    const check = validateSchedule(original,applied,data.schedule);
    if (!check.ok) return invalid(check.conflicts.map(c => c.message));
    const summary = summarize(original,data.schedule,[]);
    const accepted = { id: 'recovery-' + JSON.stringify(data.schedule.map(s => [s.cueId,s.start,s.duration])),
      plan: clone(original), scenario: clone(applied), schedule: clone(data.schedule), conflicts: [], summary, cost: summary.cost,
      changes: data.schedule.filter(s => s.start !== original.cues.find(c => c.id === s.cueId).plannedStart || s.duration !== original.cues.find(c => c.id === s.cueId).duration)
        .map(s => { const c = original.cues.find(c => c.id === s.cueId); return { cueId: c.id, fromStart: c.plannedStart, toStart: s.start, fromDuration: c.duration, toDuration: s.duration }; }) };
    const expected = exportPlan(accepted);
    if (canonical(data.plan) !== canonical(expected.plan) || canonical(data.changes) !== canonical(expected.changes) ||
        canonical(data.summary) !== canonical(expected.summary)) return invalid(['Revised plan or tradeoffs do not match the accepted recovery.']);
    const replay = evaluate(data.plan,data.scenario);
    if (replay.conflicts.length || JSON.stringify(replay.schedule.map(s => [s.cueId,s.start,s.duration])) !== JSON.stringify(data.schedule.map(s => [s.cueId,s.start,s.duration]))) {
      return invalid(['Accepted schedule cannot replay.']);
    }
    return { ok: true, errors: [], plan: clone(data.plan), scenario: clone(data.scenario), accepted };
  }
  const api = Object.freeze({ version: 1, limits: LIMITS, validate, evaluate, repair, exportPlan, validateSchedule, readInput });
  root.CueRescue = api;
  if (typeof module === 'object' && module.exports) module.exports = api;
})(typeof globalThis === 'object' ? globalThis : this);
