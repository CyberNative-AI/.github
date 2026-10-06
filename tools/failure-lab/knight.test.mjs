import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import vm from "node:vm";

const html = await readFile(new URL("./knight2012.html", import.meta.url), "utf8");
const modelMatch = html.match(/\/\* MODEL-START \*\/([\s\S]*?)\/\* MODEL-END \*\//);
assert.ok(modelMatch, "pure model block exists");
const sandbox = {};
vm.runInNewContext(modelMatch[1] + "\nglobalThis.__model = { simulate, rollbackComparison };", sandbox);
const { simulate, rollbackComparison } = sandbox.__model;

const recordSetup = {
  deployment: "manual",
  featureFlag: "reuse",
  deadCode: "leave"
};

test("record path fails and places the cause on the eighth server", () => {
  const result = simulate(recordSetup);
  assert.equal(result.ok, false);
  assert.equal(result.cause.server, 8);
  assert.match(result.cause.description, /eighth server/i);
  assert.equal(result.timeline[0].time, "9:30 a.m.");
  assert.equal(result.timeline[0].orderCount, 1);
  assert.equal(result.timeline.at(-1).orderCount, 46);
});

test("rollback causes more modeled accumulation than no rollback", () => {
  const rolledBack = simulate({ ...recordSetup, response: "rollback" });
  const continued = simulate({ ...recordSetup, response: "continue" });
  assert.equal(rolledBack.ok, false);
  assert.equal(rolledBack.timeline.at(-1).serversRunningFault, 8);
  assert.ok(rolledBack.timeline.at(-1).orderCount > continued.timeline.at(-1).orderCount);
  assert.equal(rolledBack.timeline.at(-1).orderCount, 368);
});

test("rollback reveal compares simulation-derived counts and labels them illustrative", () => {
  const rolledBack = simulate({ ...recordSetup, response: "rollback" });
  const continued = simulate({ ...recordSetup, response: "continue" });
  const comparison = rollbackComparison(rolledBack, continued);
  const match = comparison.match(/Without the rollback, this model reaches (\d+) units by ([^;]+); with it, (\d+) \(illustrative model units\)\./);
  assert.ok(match, "comparison sentence includes both counts and the illustrative label");
  assert.equal(Number(match[1]), continued.timeline.at(-1).orderCount);
  assert.equal(match[2], continued.timeline.at(-1).time);
  assert.equal(Number(match[3]), rolledBack.timeline.at(-1).orderCount);
  assert.ok(Number(match[3]) > Number(match[1]), "rollback figure is larger than continued figure");
});

test("each safe deployment, flag, or unused-code choice avoids the modeled failure", () => {
  const safeChoices = [
    { ...recordSetup, deployment: "verified" },
    { ...recordSetup, featureFlag: "new" },
    { ...recordSetup, deadCode: "remove" }
  ];
  for (const state of safeChoices) {
    const result = simulate(state);
    assert.equal(result.ok, true);
    assert.equal(result.cause, null);
    assert.equal(result.timeline.at(-1).orderCount, 0);
  }
});

test("halting stops accumulation at every point in the timeline", () => {
  const result = simulate({ ...recordSetup, response: "halt" });
  assert.equal(result.ok, true);
  assert.equal(result.cause.server, 8);
  assert.deepEqual(Array.from(result.timeline, (point) => point.orderCount), [0, 0, 0, 0, 0, 0]);
});

test("the choose screen contains no incident spoilers", () => {
  const choose = html.slice(html.indexOf('<section class="panel screen" id="choose"'), html.indexOf('<section class="panel screen" id="run"'));
  assert.doesNotMatch(choose, /Power Peg|eighth server|missed server|rollback|cause|incident|failure|loss/i);
  assert.match(choose, /Illustrative effort/);
});

test("the page does not claim a counterfactual rescue or mission outcome", () => {
  assert.doesNotMatch(html, /would\s+have\s+been\s+saved/i);
  assert.doesNotMatch(html, /\bmission\b/i);
});

test("the page has no external resources, requests, or network URLs", () => {
  assert.doesNotMatch(html, /<script\s+[^>]*src=/i);
  assert.doesNotMatch(html, /<link\s+[^>]*rel=["']stylesheet/i);
  assert.doesNotMatch(html, /<(?:img|iframe|audio|video|source|object|embed)\b[^>]*\bsrc=/i);
  assert.doesNotMatch(html, /url\(\s*["']?https?:/i);
  assert.doesNotMatch(html, /\b(fetch|XMLHttpRequest|sendBeacon|gtag|analytics)\s*\(/i);
  assert.doesNotMatch(html, /https?:\/\//i);
});

test("timeline, reduced-motion handling, keyboard-native controls, and live outcomes are present", () => {
  assert.match(html, /9:30 a\.m\./);
  assert.match(html, /10:15 a\.m\./);
  assert.match(html, /prefers-reduced-motion: reduce/);
  assert.match(html, /if \(reducedMotion\)/);
  assert.match(html, /type="radio"/);
  assert.match(html, /aria-live="polite"/);
});

test("all six on-page source identifiers have a matching register entry", () => {
  for (const id of ["S1", "S2", "S3", "S4", "S5", "S6"]) {
    assert.match(html, new RegExp('id="source-' + id + '"'));
    assert.match(html, new RegExp('href="#source-' + id + '"'));
  }
  assert.match(html, /August 1, 2012/);
  assert.match(html, /flag that had previously activated Power Peg/);
});

test("¶15 says Knight had no second-technician review or written procedure requiring one", () => {
  assert.match(html, /Knight did not have a second technician review the deployment and had no written procedures requiring that review/i);
  assert.doesNotMatch(html, /no second technician review caught the gap/i);
});

test("text and control colors meet the Failure Lab contrast convention", () => {
  const colors = Object.fromEntries(
    [...html.matchAll(/--([\w-]+):\s*(#[0-9a-fA-F]{6})\s*;/g)].map((match) => [match[1], match[2]])
  );
  const luminance = (hex) => {
    const channels = hex.slice(1).match(/.{2}/g).map((channel) => parseInt(channel, 16) / 255);
    const linear = channels.map((channel) => channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4);
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
  };
  const contrast = (first, second) => {
    const a = luminance(first);
    const b = luminance(second);
    return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
  };
  for (const [foreground, background] of [
    [colors.paper, colors.navy], [colors.paper, colors.panel], [colors.paper, colors["panel-raised"]],
    [colors.muted, colors.navy], [colors.muted, colors.panel], [colors.muted, colors["panel-raised"]],
    [colors.amber, colors.navy], [colors.amber, colors["panel-raised"]], [colors.ink, colors.amber],
    [colors.red, colors.panel], [colors.focus, colors.navy], [colors.focus, colors.panel]
  ]) assert.ok(contrast(foreground, background) >= 4.5, foreground + " on " + background + " is below 4.5:1");
  for (const background of [colors.navy, colors.panel, colors["panel-raised"]]) {
    assert.ok(contrast(colors.line, background) >= 3, colors.line + " border on " + background + " is below 3:1");
  }
  assert.ok(contrast(colors.paper, "#27384e") >= 4.5, "disabled button text is below 4.5:1");
});
