/* Original local interface. Scheduling and repair belong exclusively to CueRescue. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const clone = value => JSON.parse(JSON.stringify(value));
  const emptyScenario = () => ({ delays: [], unavailable: [] });
  const engine = globalThis.CueRescue;
  let plan, initialPlan, scenario = emptyScenario(), result = null, selected = null, accepted = null, editing = null, busy = false;
  function node(tag, text, className) { const n = document.createElement(tag); if (text !== undefined) n.textContent = String(text); if (className) n.className = className; return n; }
  function say(text, success = false) { $('message').textContent = text; $('message').className = 'message' + (success ? ' success' : ''); $('message').hidden = false; }
  function errors(v) { return (v.errors || []).map(e => typeof e === 'string' ? e : e.message || JSON.stringify(e)).join('\n') || 'The plan could not be validated.'; }
  function example(kind) {
    const cutoff = kind === 'tight' || kind === 'flexible' ? 45 : 60;
    return { version: 1, title: 'Community arts rehearsal', horizon: { start: 0, end: cutoff }, resources: [{ id: 'tech', label: 'Shared technician' }], cues: [
      { id: 'A', title: 'Opening & sound check', room: 'Room 1', plannedStart: 0, duration: 20, minDuration: 20, locked: kind === 'locked', notBefore: 0, deadline: cutoff, resources: ['tech'], priority: 3 },
      { id: 'B', title: 'Poetry microphone session', room: 'Room 2', plannedStart: 20, duration: 20, minDuration: 15, locked: false, notBefore: 20, deadline: cutoff, resources: ['tech'], priority: 2 },
      { id: 'C', title: 'Movement rehearsal', room: 'Room 1', plannedStart: 20, duration: 20, minDuration: kind === 'flexible' ? 15 : 20, locked: false, notBefore: 20, deadline: cutoff, resources: [], priority: 2 }
    ] };
  }
  function checked(value) { const v = engine.validate(value); if (!v.ok) throw new Error(errors(v)); return value; }
  function clearDerived() { result = null; selected = null; accepted = null; }
  function decode(value) { const d=engine.readInput(value);if(!d.ok)throw new Error(errors(d));return d; }
  function load(value, notice) {
    const d=decode(value); plan=clone(d.plan);initialPlan=clone(value);scenario=clone(d.scenario);clearDerived();
    if(d.accepted){const original=d.accepted;accepted={beforePlan:clone(original.plan),beforeScenario:clone(original.scenario),plan:clone(d.plan),replayScenario:clone(d.scenario),saved:clone(value),diff:changes(rows(engine.evaluate(d.plan,d.scenario),d.plan),original.plan)};}
    render();if(notice)say(notice,true);
  }
  function rows(evaluation, source = plan) {
    const raw = evaluation.schedule;
    const list = Array.isArray(raw) ? raw : raw && typeof raw === 'object' ? Object.entries(raw).map(([id, row]) => ({ id, ...row })) : [];
    return source.cues.map(cue => {
      const row = list.find(r => (r.cueId || r.id) === cue.id);
      if (!row) throw new Error('The engine did not return a schedule for cue ' + cue.id + '.');
      const start = row.start ?? row.plannedStart, duration = row.duration ?? (row.end - start), end = row.end ?? (start + duration);
      if (![start, duration, end].every(Number.isFinite)) throw new Error('The engine returned an unreadable schedule for cue ' + cue.id + '.');
      return { ...cue, ...row, id: cue.id, title: cue.title, room: cue.room, start, duration, end };
    });
  }
  function optionInput(option) { const saved=engine.exportPlan(option);return {...decode(saved),saved}; }
  function evaluated(value, sc) { const e = engine.evaluate(value, sc); return { evaluation: e, schedule: rows(e, value) }; }
  function changes(schedule, base) { return schedule.map(r => { const c = base.cues.find(c => c.id === r.id); return { id: r.id, title: r.title, before: c.plannedStart, after: r.start, delay: r.start - c.plannedStart, shortened: c.duration - r.duration, beforeDuration: c.duration, duration: r.duration }; }); }
  function totals(diff) { return { late: diff.reduce((n,d) => n + Math.max(0,d.delay),0), shortened: diff.reduce((n,d) => n + Math.max(0,d.shortened),0) }; }
  function selectedEvaluation() { if (selected !== null && result) {const d=optionInput(result.options[selected]);return evaluated(d.plan,d.scenario);} return evaluated(plan, scenario); }
  function resourceLabel(id) { return plan.resources.find(r => r.id === id)?.label || id; }
  function cueLabel(id) { const c = plan.cues.find(c => c.id === id); return c ? c.id + ' · ' + c.title : id; }
  function renderTimeline(schedule) {
    const base = accepted ? accepted.beforePlan : plan;
    const host = $('timeline'); host.replaceChildren();
    const axis = node('div', undefined, 'time-axis'); [0,.25,.5,.75,1].forEach(t => axis.append(node('span', Math.round(plan.horizon.start + t*(plan.horizon.end-plan.horizon.start))))); host.append(axis);
    [...new Set(plan.cues.map(c=>c.room))].forEach(room => {
      const lane = node('div', undefined, 'room'); lane.append(node('div', room, 'room-title'));
      schedule.filter(c=>c.room===room).forEach(c => {
        const old = base.cues.find(b=>b.id===c.id) || c, line = node('div', undefined, 'cue-line'), meta = node('div', undefined, 'cue-meta');
        meta.append(node('strong', c.id + ' · ' + c.title),node('span', c.start+'–'+c.end+' min'));
        const track = node('div',undefined,'track'); track.setAttribute('aria-hidden','true');
        const position = (el,start,duration) => { const h=plan.horizon; el.style.left = (Math.max(h.start,Math.min(h.end,start))-h.start)/(h.end-h.start)*100+'%'; el.style.width = Math.max(0,Math.min(h.end,start+duration)-Math.max(h.start,start))/(h.end-h.start)*100+'%'; };
        const ghost = node('span',undefined,'ghost');position(ghost,old.plannedStart,old.duration);track.append(ghost);
        const changed = c.start !== old.plannedStart || c.duration !== old.duration;
        const bar = node('span',undefined,'bar'+(changed?' changed':'')+(selected!==null?' preview':'')+(c.locked?' locked':''));position(bar,c.start,c.duration);track.append(bar);
        line.append(meta,track);lane.append(line);
      });host.append(lane);
    });
    $('timelineMode').textContent = accepted ? 'Accepted recovery' : selected!==null ? 'Recovery preview' : scenario.delays.length||scenario.unavailable.length ? 'Disrupted plan' : 'Original plan';
    $('timelineCaption').textContent = 'Minute '+plan.horizon.start+' is the window start. Dashed outlines show original times; the right rule is the hard cutoff. Exact times are printed beside each cue.';
  }
  function conflictText(c) {
    if (typeof c === 'string') return { title:'Constraint conflict', detail:c };
    const kind = c.type || c.kind || c.code || 'constraint';
    const ids = c.cueIds || c.cues || [c.cueId,c.otherCueId].filter(Boolean);
    const names = ids.map(i=>typeof i==='string'?cueLabel(i):i.id||i.cueId||'Cue').join(' + ');
    const where = c.resourceId ? resourceLabel(c.resourceId) : c.room || c.roomId || '';
    const time = Number.isFinite(c.start) && Number.isFinite(c.end) ? ' · '+c.start+'–'+c.end+' min' : '';
    return { title: c.message || (String(kind).replaceAll('_',' ') + (where?' · '+where:'')), detail: names + time || c.reason || 'This constraint is not satisfied in the current schedule.' };
  }
  function renderConflicts(evaluation) {
    const list = evaluation.conflicts || [], host=$('conflicts');host.replaceChildren();
    $('conflictCount').textContent=list.length ? list.length+' conflict'+(list.length===1?'':'s') : 'CLEAR';
    if (!list.length) host.append(node('p','No conflicts in this schedule. All reported constraints are satisfied.','clear-check'));
    list.forEach(c=>{const row=node('div',undefined,'conflict-row'), body=node('div'), text=conflictText(c);body.append(node('h3',text.title),node('p',text.detail));row.append(node('span','!','conflict-icon'),body);host.append(row)});
    const disrupted=scenario.delays.length||scenario.unavailable.length;
    $('recoveryStatus').className='recovery-status'+(list.length?' problem':'');
    $('statusHeadline').textContent=accepted?'Accepted plan is ready':selected!==null?'Preview is clear':list.length?'This plan needs recovery':disrupted?'Disruption fits the current plan':'Ready for a rehearsal';
    $('statusDetail').textContent=accepted?'Download and reload the revised JSON to reproduce it.':selected!==null?'Compare its changes below. Accept it to update the plan.':list.length?'Room, resource or hard-limit conflicts are listed alongside the timeline.':disrupted?'You can still compare feasible recovery choices.':'Introduce a disruption to see what needs to change.';
  }
  function cell(label,text) { const c=node('div',undefined,'ledger-cell');c.append(node('span',label,'eyebrow'),node('span',text));return c; }
  function renderLedger() {
    const host=$('cueRows');host.replaceChildren();
    plan.cues.forEach(c=>{const row=node('div',undefined,'ledger-row'), title=node('div',undefined,'ledger-title');title.append(node('strong',c.title),node('span',c.room+' · '+(c.resources.map(resourceLabel).join(', ')||'No shared resource')));const edit=node('button','Edit','quiet');edit.setAttribute('aria-label','Edit cue '+c.id);edit.addEventListener('click',()=>editCue(c.id));row.append(node('span',c.id,'cue-id'),title,cell('PLANNED',c.plannedStart+'–'+(c.plannedStart+c.duration)+' min'),cell('DURATION',c.duration+' min / min '+c.minDuration),cell('HARD LIMITS','≥'+c.notBefore+' / ≤'+c.deadline+' · '+(c.locked?'LOCKED':'unlocked')+' · P'+c.priority),edit);host.append(row)});
  }
  function renderScenario() {
    $('scenarioList').replaceChildren();
    scenario.delays.forEach(d=>$('scenarioList').append(node('div',cueLabel(d.cueId)+' · +'+d.minutes+' min','scenario-item')));
    scenario.unavailable.forEach(u=>$('scenarioList').append(node('div',resourceLabel(u.resourceId)+' unavailable · '+u.start+'–'+u.end+' min','scenario-item')));
    const oldCue=$('delayCue').value,oldRes=$('unavailableResource').value;
    $('delayCue').replaceChildren(...plan.cues.map(c=>{const o=node('option',c.id+' · '+c.title);o.value=c.id;return o}));
    if(plan.cues.some(c=>c.id===oldCue))$('delayCue').value=oldCue;
    $('unavailableResource').replaceChildren(...plan.resources.map(r=>{const o=node('option',r.label);o.value=r.id;return o}));if(plan.resources.some(r=>r.id===oldRes))$('unavailableResource').value=oldRes;
    $('unavailableForm').querySelector('button').disabled=!plan.resources.length;
    $('clearScenario').disabled=!(scenario.delays.length||scenario.unavailable.length);
    $('quickDelay').disabled=!plan.cues.length; $('quickDelay').textContent='Try cue '+plan.cues[0].id+' 10 minutes late ↗';
  }
  function renderOptions() {
    $('choices').hidden=!result||!!accepted; $('accepted').hidden=!accepted; $('options').replaceChildren();
    if (!result) return;
    const s=result.search||{};
    $('searchNote').textContent=(s.examined??'Unreported')+' candidate placements examined. '+(s.exhaustive?'Search exhausted the defined candidate space.':'Bounded search; other feasible choices may exist.')+' '+(s.stoppedBecause?'Stopped: '+s.stoppedBecause+'.':'')+' Cost = sum of priority × (minutes later + 3 × minutes shortened). No best-plan claim for a bounded search.';
    if(!result.options.length){$('options').append(node('p',result.noSolutionReason||'No feasible recovery was found within this search. The plan and disruptions are unchanged.','form-error'));}
    result.options.forEach((o,i)=>{
      const decoded=optionInput(o),value=decoded.plan, view=evaluated(value,decoded.scenario), diff=changes(view.schedule,plan), t=totals(diff), box=node('div',undefined,'option'+(selected===i?' chosen':''));
      if(view.evaluation.conflicts.length) throw new Error('The engine offered a recovery with conflicts. It cannot be accepted.');
      box.append(node('h4','Choice '+(i+1)+(selected===i?' · SELECTED':'')));
      const stats=node('div',undefined,'tradeoffs');for(const [number,label]of [[t.late,'total minutes later'],[t.shortened,'minutes shortened']]){const stat=node('div');stat.append(node('strong',number),node('span',label));stats.append(stat)}box.append(stats);
      box.append(node('p',diff.map(d=>d.id+': '+d.before+' → '+d.after+' min'+(d.shortened?' · −'+d.shortened+' min duration':' · full duration')).join('; ')));
      box.append(node('p','Cutoff '+plan.horizon.end+' min. '+value.cues.map(c=>c.id+' / '+c.room+': min '+c.minDuration+', not before '+c.notBefore+', deadline '+c.deadline+(c.locked?', locked':', unlocked')+'; '+(c.resources.map(resourceLabel).join(', ')||'no shared resource')).join(' · ')));
      if(o.cost!==undefined)box.append(node('p','Engine change cost: '+(typeof o.cost==='number'?o.cost:JSON.stringify(o.cost))));
      const b=node('button',selected===i?'Selected · timeline above':'Preview this choice','quiet');b.setAttribute('aria-pressed',String(selected===i));b.addEventListener('click',()=>{selected=i;render();say('Choice '+(i+1)+' is a preview. Accept it to save the revised plan.',true)});box.append(b);$('options').append(box);
    });
    $('accept').disabled=selected===null||!result.options.length;
  }
  function render() {
    try {
      $('planTitle').textContent=plan.title;$('cutoff').textContent=plan.horizon.end+' min';$('windowText').textContent=plan.horizon.start+'–'+plan.horizon.end+' minute window';
      const roomCount=new Set(plan.cues.map(c=>c.room)).size;
      document.querySelector('.intro .eyebrow').textContent=roomCount+' ROOM'+(roomCount===1?'':'S')+'. '+plan.resources.length+' SHARED RESOURCE'+(plan.resources.length===1?'':'S')+'.';
      const {evaluation,schedule}=selectedEvaluation();renderTimeline(schedule);renderConflicts(evaluation);renderLedger();renderScenario();renderOptions();
      if(accepted){const t=totals(accepted.diff);$('acceptedDetail').textContent=t.late+' total cue-minutes later; '+t.shortened+' minutes shortened. '+plan.cues.length+' cues retained. Hard limits unchanged.';renderSheet()}
    }catch(e){say('Unable to display this engine result: '+e.message);$('compute').disabled=true;$('accept').disabled=true;}
  }
  function scenarioChange(next) { scenario=next; clearDerived();render();$('message').hidden=true; }
  function int(id) { const n=Number($(id).value);if($(id).value.trim()===''||!Number.isSafeInteger(n))throw new Error('Enter a whole number of minutes.');return n; }
  $('loadExample').addEventListener('click',()=>{try{load(example($('example').value),'Synthetic example loaded. Apply a disruption to rehearse recovery.')}catch(e){say(e.message)}});
  $('reset').addEventListener('click',()=>load(initialPlan,'Rehearsal reset to the last loaded plan.'));
  $('delayForm').addEventListener('submit',e=>{e.preventDefault();try{const minutes=int('delayMinutes');if(minutes<1||minutes>720)throw new Error('Use a delay from 1 to 720 minutes.');const cueId=$('delayCue').value;scenarioChange({...scenario,delays:[...scenario.delays.filter(d=>d.cueId!==cueId),{cueId,minutes}]})}catch(err){say(err.message)}});
  $('quickDelay').addEventListener('click',()=>{scenarioChange({...scenario,delays:[...scenario.delays.filter(d=>d.cueId!==plan.cues[0].id),{cueId:plan.cues[0].id,minutes:10}]})});
  $('unavailableForm').addEventListener('submit',e=>{e.preventDefault();try{const start=int('unavailableStart'),end=int('unavailableEnd');if(start<plan.horizon.start||end>plan.horizon.end||start>=end)throw new Error('Unavailability must be a positive interval inside the planning window.');scenarioChange({...scenario,unavailable:[...scenario.unavailable,{resourceId:$('unavailableResource').value,start,end}]})}catch(err){say(err.message)}});
  $('clearScenario').addEventListener('click',()=>scenarioChange(emptyScenario()));
  $('compute').addEventListener('click',()=>{
    if(busy)return;busy=true;$('compute').disabled=true;$('compute').textContent='Searching up to 5,000 candidates…';$('message').hidden=true;
    // Give the searching status a paint before the bounded, synchronous v1 engine call.
    requestAnimationFrame(()=>setTimeout(()=>{try{const r=engine.repair(clone(plan),clone(scenario),{maxCandidates:5000,maxOptions:3});result=r;selected=null;accepted=null;render();say(r.options.length?r.options.length+' feasible recovery choices. Preview one, then accept it.':r.noSolutionReason||'No feasible option was found within the bounded search.',!!r.options.length)}catch(e){say('Recovery search failed. Your plan is unchanged. '+e.message)}finally{busy=false;$('compute').disabled=false;const arrow=node('span','→');arrow.setAttribute('aria-hidden','true');$('compute').replaceChildren(document.createTextNode('Find recovery choices '),arrow)}},0));
  });
  $('accept').addEventListener('click',()=>{
    try{if(selected===null||!result)return;const decoded=optionInput(result.options[selected]),value=clone(decoded.plan), view=evaluated(value,decoded.scenario);if(view.evaluation.conflicts.length)throw new Error('This recovery still has conflicts.');const beforePlan=clone(plan),beforeScenario=clone(scenario);accepted={beforePlan,beforeScenario,plan:clone(value),replayScenario:clone(decoded.scenario),saved:clone(decoded.saved),diff:changes(view.schedule,beforePlan)};plan=value;scenario=clone(decoded.scenario);result=null;selected=null;render();say('Recovery accepted. Revised JSON and cue sheet are ready to download.',true)}catch(e){say('Recovery was not accepted: '+e.message)}
  });
  $('undo').addEventListener('click',()=>{if(!accepted)return;plan=accepted.beforePlan;scenario=accepted.beforeScenario;clearDerived();render();say('Acceptance undone. The disrupted plan is restored.',true)});
  function download(name,text,type) {const url=URL.createObjectURL(new Blob([text],{type})),link=node('a');link.href=url;link.download=name;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000)}
  $('export').addEventListener('click',()=>{if(accepted){download('cue-rescue-revised.json',JSON.stringify(accepted.saved,null,2)+'\n','application/json');say('Revised JSON downloaded. Import it to reproduce this accepted schedule.',true)}});
  $('importButton').addEventListener('click',()=>$('fileInput').click());
  $('fileInput').addEventListener('change',async()=>{const file=$('fileInput').files[0];if(!file)return;try{if(file.size>131072)throw new Error('The JSON file exceeds 128 KiB.');const value=JSON.parse(await file.text());load(value,'JSON loaded. Saved timing and availability constraints are reproduced; accepted delays are already included.')}catch(e){say('Import rejected; your last valid plan and rehearsal are unchanged. '+e.message)}finally{$('fileInput').value=''}});
  function field(label,name,value,type='text',wide=false) {const l=node('label',label,wide?'wide':''),input=node('input');input.name=name;input.type=type;if(type==='checkbox'){input.checked=value;l.className='check-label';input.required=false;}else{input.value=value;input.required=true;if(type==='number')input.step='1';else input.maxLength=160;}l.append(input);return l;}
  function editCue(id) {
    const c=plan.cues.find(c=>c.id===id)||{id:'cue-'+(plan.cues.length+1),title:'New cue',room:plan.cues[0]?.room||'Room 1',plannedStart:plan.horizon.start,duration:10,minDuration:10,locked:false,notBefore:plan.horizon.start,deadline:plan.horizon.end,resources:[],priority:1};editing=id||null;
    $('cueDialogTitle').textContent=editing?'Edit cue '+c.id:'Add cue';$('cueError').textContent='';$('deleteCue').hidden=!editing;
    const f=$('cueFields');f.replaceChildren(field('Cue ID','id',c.id),field('Title','title',c.title,'text',true),field('Room','room',c.room));
    [['Planned start','plannedStart'],['Duration (minutes)','duration'],['Minimum duration','minDuration'],['Not before minute','notBefore'],['Deadline minute','deadline'],['Priority (1–3)','priority']].forEach(([label,name])=>f.append(field(label,name,c[name],'number')));
    f.append(field('Lock exact start & duration','locked',c.locked,'checkbox'));
    const fs=node('fieldset');fs.append(node('legend','Resources occupied for the whole cue'));if(!plan.resources.length)fs.append(node('p','No resources in this plan.'));plan.resources.forEach(r=>{const l=field(r.label,'resource',c.resources.includes(r.id),'checkbox');l.querySelector('input').value=r.id;fs.append(l)});f.append(fs);$('cueDialog').showModal();
  }
  $('addCue').addEventListener('click',()=>editCue(null));
  function applyEdit(next) {checked(next);plan=clone(next);scenario=emptyScenario();clearDerived();render();say('Plan updated. Disruptions were cleared; rehearse the revised constraints.',true)}
  $('cueForm').addEventListener('submit',e=>{e.preventDefault();try{const f=new FormData(e.target), c={id:f.get('id').trim(),title:f.get('title').trim(),room:f.get('room').trim(),locked:f.has('locked'),resources:f.getAll('resource')};['plannedStart','duration','minDuration','notBefore','deadline','priority'].forEach(k=>c[k]=Number(f.get(k)));const next=clone(plan);if(editing)next.cues[next.cues.findIndex(c=>c.id===editing)]=c;else next.cues.push(c);applyEdit(next);$('cueDialog').close()}catch(err){$('cueError').textContent=err.message}});
  $('deleteCue').addEventListener('click',()=>{try{const next=clone(plan);next.cues=next.cues.filter(c=>c.id!==editing);applyEdit(next);$('cueDialog').close()}catch(e){$('cueError').textContent=e.message}});
  $('editPlan').addEventListener('click',()=>{$('planName').value=plan.title;$('planStart').value=plan.horizon.start;$('planEnd').value=plan.horizon.end;$('planResources').value=plan.resources.map(r=>r.id+','+r.label).join('\n');$('planError').textContent='';$('planDialog').showModal()});
  $('planForm').addEventListener('submit',e=>{e.preventDefault();try{const next=clone(plan);next.title=$('planName').value.trim();next.horizon={start:int('planStart'),end:int('planEnd')};next.resources=$('planResources').value.split('\n').filter(l=>l.trim()).map(l=>{const at=l.indexOf(',');if(at<1)throw new Error('Each resource needs an id, then a comma, then a label.');return{id:l.slice(0,at).trim(),label:l.slice(at+1).trim()}});applyEdit(next);$('planDialog').close()}catch(err){$('planError').textContent=err.message}});
  document.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click',()=>b.closest('dialog').close()));
  function sheetContent() {
    const content=node('section'), view=evaluated(accepted.plan,accepted.replayScenario);content.append(node('h1',accepted.plan.title),node('p','Accepted recovery · minutes from the planning-window start · hard cutoff '+plan.horizon.end+' min'));
    const scroll=node('div',undefined,'sheet-scroll'),table=node('table',undefined,'sheet-table'),head=node('thead'),tr=node('tr');['Cue / room','Revised time','Duration / minimum','Resources','Hard limits','Change from original'].forEach(t=>tr.append(node('th',t)));head.append(tr);table.append(head);const body=node('tbody');
    view.schedule.forEach(c=>{const d=accepted.diff.find(d=>d.id===c.id),row=node('tr');[c.id+' · '+c.title+' / '+c.room,c.start+'–'+c.end+' min'+(c.locked?' · LOCKED':''),c.duration+' / '+c.minDuration+' min',c.resources.map(resourceLabel).join(', ')||'None','Not before '+c.notBefore+'; deadline '+c.deadline+'; '+(c.locked?'locked':'unlocked'),(d.delay?'Start '+(d.delay>0?'+':'')+d.delay+' min':'Start unchanged')+'; '+(d.shortened?'duration −'+d.shortened+' min':'full duration')].forEach(t=>row.append(node('td',t)));body.append(row)});table.append(body);scroll.append(table);content.append(scroll);
    const notes=node('div',undefined,'sheet-notes');notes.append(node('h3','Rehearsed disruption'));accepted.beforeScenario.delays.forEach(d=>notes.append(node('p',cueLabel(d.cueId)+' delayed '+d.minutes+' min')));accepted.beforeScenario.unavailable.forEach(u=>notes.append(node('p',resourceLabel(u.resourceId)+' unavailable '+u.start+'–'+u.end+' min')));notes.append(node('p','Every cue remains in its original room. Resource occupancy covers the whole cue. This is a private planning artifact, not live show control or a staffing promise.'),node('p','CyberNative AI LLC · Reload the revised JSON to reproduce the accepted schedule.'));content.append(notes);return content;
  }
  function renderSheet() {$('printArea').replaceChildren(sheetContent())}
  $('sheetView').addEventListener('click',()=>{if(accepted){renderSheet();$('sheetDialog').showModal()}});
  $('sheetDownload').addEventListener('click',()=>{if(!accepted)return;const doc=document.implementation.createHTMLDocument('Cue Rescue · Accepted cue sheet');doc.documentElement.lang='en';const meta=node('meta');meta.name='viewport';meta.content='width=device-width, initial-scale=1';doc.head.append(meta);const style=node('style','body{font:16px/1.5 Arial,sans-serif;color:#0e1427;margin:32px;max-width:1100px}h1{font:36px Georgia,serif}table{width:100%;border-collapse:collapse;margin:24px 0}th,td{text-align:left;padding:12px;border-bottom:1px solid #b0b0b0;vertical-align:top}th{font-size:13px}.sheet-scroll{overflow-x:auto}.sheet-notes{border-top:2px solid #0e1427;padding-top:16px}@media print{body{margin:0}.sheet-scroll{overflow:visible}}');doc.head.append(style);doc.body.append(doc.importNode(sheetContent(),true));download('cue-rescue-cue-sheet.html','<!doctype html>\n'+doc.documentElement.outerHTML,'text/html');say('Printable cue sheet downloaded, including the revised times and changes.',true)});
  $('print').addEventListener('click',()=>window.print());
  if(!engine){$('engineNote').hidden=false;$('engineNote').textContent='The recovery engine is missing. Place the matching engine.js beside this interface and reload. No schedule can be computed.';document.querySelectorAll('button,input,select').forEach(e=>e.disabled=true);return;}
  if(engine.fixture){$('engineNote').hidden=false;$('engineNote').textContent='INTERFACE FIXTURE — synthetic precomputed values only. This screen does not yet verify the recovery engine.';}
  try{load(example('standard'));}catch(e){say('The example could not load: '+e.message)}
})();
