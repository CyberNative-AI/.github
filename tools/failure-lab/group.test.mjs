// Facilitator mode: session state, model custody, sourcing and the no-network boundary.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const read = (name) => readFileSync(new URL("./" + name, import.meta.url), "utf8");
const block = (text) => text.match(/\/\* MODEL-START \*\/[\s\S]*?\/\* MODEL-END \*\//)[0];

const context = vm.createContext({});
for (const file of ["group-core.js", "group-ariane.js", "group-knight.js"]) vm.runInContext(read(file), context, { filename: file });
const G = context.FailureLabGroup;
const ariane = G.get("ariane");
const knight = G.get("knight");
const plain = (value) => JSON.parse(JSON.stringify(value));

function play(scenario, steps) {
  let session = G.createSession(scenario);
  for (const [id, value, tally] of steps) session = G.recordChoice(scenario, session, id, value, tally || null);
  return session;
}

test("each group scenario carries its page's model byte for byte", () => {
  assert.equal(block(read("group-ariane.js")), block(read("ariane501.html")));
  assert.equal(block(read("group-knight.js")), block(read("knight2012.html")));
});

test("every discussion question, lesson and record note cites a source in the register", () => {
  for (const s of [ariane, knight]) {
    assert.ok(s.questions.length >= 3 && s.questions.length <= 5, s.id + " has 3–5 questions");
    const cited = [...s.questions, ...s.lessons, ...s.history.items, ...s.brief.points, ...s.decisions.map((d) => d.recordNote)];
    for (const item of cited) {
      assert.ok(item.sources.length > 0, "cited: " + item.text.slice(0, 40));
      for (const id of item.sources) assert.ok(s.sources[id], s.id + " cites registered " + id);
    }
    // Register IDs match the page's own S1–S6 register.
    const page = read(s.page);
    for (const id of Object.keys(s.sources)) assert.match(page, new RegExp('id="source-' + id + '"'));
  }
});

test("register() refuses a question without a known source", () => {
  const bad = { ...knight, id: "bad", questions: [...knight.questions.slice(0, 2), { text: "Unsourced?", sources: ["S9"] }] };
  assert.throws(() => G.register(bad), /unknown source S9/);
});

test("a recorded choice and tally appear in the debrief, against the record", () => {
  const session = play(knight, [
    ["deployment", "verified", { manual: 2, verified: 7 }],
    ["featureFlag", "reuse"],
    ["deadCode", "leave"]
  ]);
  const d = G.debrief(knight, session);
  const row = d.rows.find((r) => r.id === "deployment");
  assert.equal(row.chosenLabel, "Automated deploy with per-server verification");
  assert.equal(row.recordLabel, "Copy to each server manually");
  assert.equal(row.matchesRecord, false);
  assert.equal(row.tallyText, "Manual 2 · Verified 7 (9 hands)");
  assert.equal(d.rows.find((r) => r.id === "featureFlag").tally, null);
  assert.equal(d.outcome.title, "No repeated-order failure in this model");
});

test("the summary lists every decision, including one the run never reached", () => {
  const safe = G.summary(knight, play(knight, [["deployment", "manual"], ["featureFlag", "new"], ["deadCode", "leave"]]));
  assert.deepEqual(plain(safe.decisions.map((r) => r.title)), ["Deployment", "Feature flag", "Unused code", "Response at the open"]);
  assert.match(safe.decisions[3].group, /^Not reached/);
  assert.equal(safe.decisions[3].record, "Roll back the new code");

  const full = G.summary(knight, play(knight, [["deployment", "manual"], ["featureFlag", "reuse"], ["deadCode", "leave"], ["response", "halt", { rollback: 1, halt: 9 }]]));
  assert.deepEqual(plain(full.decisions.map((r) => [r.group, r.tally])), [
    ["Copy to each server manually", ""],
    ["Reuse an existing flag", ""],
    ["Leave it in place", ""],
    ["Halt SMARS from sending orders", "Roll back 1 · Halt 9 (10 hands)"]
  ]);
  assert.equal(full.outcome.title, "The halt stops further accumulation");
  assert.ok(full.lessons.length >= 3 && full.lessons.every((l) => l.sources.length));
  assert.match(full.limits, /illustrative/);
  assert.match(full.limits, /Not a certification/);

  const a = G.summary(ariane, play(ariane, [["protect", "ABCE"], ["align", "keep"]]));
  assert.deepEqual(plain(a.decisions.map((r) => r.title)), ["Spend the protection budget", "Keep alignment running after lift-off"]);
  assert.ok(a.decisions.every((r) => r.matchesRecord));
});

test("tallies reject empty, negative and non-integer counts and accept whole numbers", () => {
  const d = knight.decisions[0];
  assert.match(G.parseTally(d, { manual: "", verified: "3" }).error, /Enter the number of hands for “Manual”/);
  assert.match(G.parseTally(d, { manual: "  ", verified: "3" }).error, /Enter the number of hands/);
  assert.match(G.parseTally(d, { manual: "-1", verified: "3" }).error, /cannot be negative/);
  assert.match(G.parseTally(d, { manual: "2.5", verified: "3" }).error, /whole number/);
  assert.match(G.parseTally(d, { manual: "1e2", verified: "3" }).error, /whole number/);
  assert.equal(G.parseTally(d, { manual: "1", verified: "x" }).field, "verified");
  assert.deepEqual(plain(G.parseTally(d, { manual: "0", verified: " 12 " })), { ok: true, counts: { manual: 0, verified: 12 } });
});

test("the incident decision appears only when the release is vulnerable, and stale answers are dropped", () => {
  let session = play(knight, [["deployment", "manual"], ["featureFlag", "reuse"], ["deadCode", "leave"]]);
  assert.equal(G.nextDecision(knight, session, "after").id, "response");
  session = G.recordChoice(knight, session, "response", "rollback", null);
  assert.match(G.debrief(knight, session).outcome.text, /reaches 46 units by 10:15 a\.m\.; with it, 368/);
  session = G.recordChoice(knight, session, "deadCode", "remove", null);
  assert.equal("response" in session.choices, false);
  assert.equal(G.hasAfterPhase(knight, session), false);
  assert.equal(G.isComplete(knight, session), true);
});

test("Ariane plans map to the page model's outcomes", () => {
  const title = (protect, align) => ariane.run({ protect, align }).title;
  assert.equal(title("ABCE", "keep"), "Ariane 5 reaches an overflow on BH");
  assert.equal(ariane.run({ protect: "ABCE", align: "keep" }).record.steps.length, 4);
  assert.equal(title("ABCE", "stop"), "Both profiles avoid the modelled failure");
  assert.equal(title("ABCBH", "keep"), "Both profiles avoid the modelled failure");
  assert.equal(title("ABC", "keep"), "Ariane 5 reaches an overflow on BH");
  assert.equal(title("ALL", "keep"), "The plan breaks the workload target");
  assert.match(ariane.run({ protect: "ALL", align: "keep" }).text, /87%/);
});

test("modelled outcomes hold model statements only; sourced history sits in a separate record block", () => {
  const outcomes = [];
  for (const protect of ["ABCE", "ABCBH", "ABC", "ALL"]) for (const align of ["keep", "stop"]) outcomes.push(ariane.run({ protect, align }, "final"));
  for (const deployment of ["manual", "verified"]) for (const featureFlag of ["reuse", "new"]) for (const deadCode of ["leave", "remove"]) {
    outcomes.push(knight.run({ deployment, featureFlag, deadCode }, "open"));
    for (const response of ["rollback", "halt"]) outcomes.push(knight.run({ deployment, featureFlag, deadCode, response }, "final"));
  }
  for (const out of outcomes) {
    assert.deepEqual(plain(out.sources), [], out.title + ": no source tags in the modelled block");
    assert.doesNotMatch(out.text, /SEC order|Inquiry Board|the report|historical account|below/i, out.title + ": no history in the modelled block");
    assert.equal((out.text.match(/profile:/g) || []).length, 0, out.title + ": no duplicated per-profile lines");
    if (out.record) for (const step of out.record.steps) assert.ok(step.sources.length, "record steps are cited");
  }
});

test("the summary cites every historical statement and marks model equivalents", () => {
  for (const [scenario, steps] of [[ariane, [["protect", "ABCE"], ["align", "keep"]]], [knight, [["deployment", "manual"], ["featureFlag", "reuse"], ["deadCode", "leave"], ["response", "rollback"]]]]) {
    const s = G.summary(scenario, play(scenario, steps));
    for (const row of s.decisions) assert.ok(row.recordSources.length, scenario.id + " record column cited: " + row.title);
    assert.ok(s.history.sources.length, "history headline cited");
    assert.ok(s.history.items.length && s.history.items.every((h) => h.sources.length), "history items cited");
    assert.equal("sources" in s.outcome, false, "modelled outcome carries no source tags");
  }
  const equivalents = (scenario, steps) => G.summary(scenario, play(scenario, steps)).decisions.filter((r) => r.recordModelEquivalent).map((r) => r.title);
  assert.deepEqual(plain(equivalents(ariane, [["protect", "ABCE"], ["align", "keep"]])), ["Spend the protection budget"]);
  assert.deepEqual(plain(equivalents(knight, [["deployment", "manual"], ["featureFlag", "reuse"], ["deadCode", "leave"]])), ["Deployment"]);
});

test("facilitator files load nothing remote and store nothing", () => {
  const files = ["group.html", "group-core.js", "group-ariane.js", "group-knight.js"];
  for (const name of files) {
    const text = read(name);
    assert.doesNotMatch(text, /https?:\/\//i, name + " has no URL");
    assert.doesNotMatch(text, /\b(fetch|XMLHttpRequest|sendBeacon|WebSocket|localStorage|sessionStorage|indexedDB|document\.cookie)\b/, name + " sends and stores nothing");
    assert.doesNotMatch(text, /@import|url\(/i, name + " imports no resources");
  }
  const html = read("group.html");
  const srcs = [...html.matchAll(/<script\s+src="([^"]+)"/g)].map((m) => m[1]);
  assert.deepEqual(srcs, ["group-core.js", "group-ariane.js", "group-knight.js"]);
  assert.doesNotMatch(html, /<(link|img|iframe|video|audio|source)\b/i);
});

test("the index reaches facilitator mode without adding script", () => {
  const index = read("index.html");
  assert.match(index, /<a class="group-entry" href="group\.html" id="group-entry">/);
  assert.match(index, /href="group\.html#ariane">Run with a group</);
  assert.match(index, /href="group\.html#knight">Run with a group</);
  assert.doesNotMatch(index, /<script/i);
});
