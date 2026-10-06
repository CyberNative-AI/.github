import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import vm from "node:vm";

const html = await readFile(new URL("./ariane501.html", import.meta.url), "utf8");
const modelMatch = html.match(/\/\* MODEL-START \*\/([\s\S]*?)\/\* MODEL-END \*\//);
assert.ok(modelMatch, "pure model block exists");
const sandbox = {};
vm.runInNewContext(modelMatch[1] + "\nglobalThis.__model = { MODEL, modelLoad, simulate, INITIAL_CHOICE, survivalReason };", sandbox);
const model = sandbox.__model;

const asFlown = { protected: ["A", "B", "C", "E"], alignAfterLiftoff: true };

test("as-flown Ariane 4 profile stays within the model limit at 78% load", () => {
  const result = model.simulate(asFlown, "A4");
  assert.equal(result.ok, true);
  assert.equal(result.load, 78);
  assert.equal(result.overBudget, false);
});

test("as-flown Ariane 5 profile fails on BH at H0 + 36.7 s", () => {
  const result = model.simulate(asFlown, "A5");
  assert.equal(result.ok, false);
  assert.equal(result.load, 78);
  assert.equal(result.failure.var, "BH");
  assert.equal(result.failure.tBackup, 36.7);
  assert.equal(result.failure.tActiveApprox, "~0.05 s later");
  assert.equal(result.failure.tBreakup, 39);
});

test("stopping alignment after lift-off avoids the modelled Ariane 5 BH failure", () => {
  const result = model.simulate({ ...asFlown, alignAfterLiftoff: false }, "A5");
  assert.equal(result.ok, true);
  assert.equal(result.failure, null);
});

test("protecting BH instead of E remains within budget and avoids failure", () => {
  const result = model.simulate({ protected: ["A", "B", "C", "BH"], alignAfterLiftoff: true }, "A5");
  assert.equal(result.ok, true);
  assert.equal(result.load, 78);
  assert.equal(result.failure, null);
});

test("protecting every conversion exceeds the workload target at 87%", () => {
  const result = model.simulate({ protected: [...model.MODEL.variables], alignAfterLiftoff: true }, "A5");
  assert.equal(result.ok, false);
  assert.equal(result.load, 87);
  assert.equal(result.overBudget, true);
  assert.equal(result.failure, null);
});

test("leaving A unprotected changes the Ariane 4 result", () => {
  const result = model.simulate({ protected: ["B", "C", "E"], alignAfterLiftoff: true }, "A4");
  assert.equal(result.ok, false);
  assert.equal(result.failure.var, "A");
  assert.equal(result.overBudget, false);
});

test("the page does not claim mission success", () => {
  assert.equal(/mission\s+success/i.test(html), false);
});

test("the page stays within its 21-word source quotation allowance", () => {
  const quotedWords = [...html.matchAll(/“([^”]+)”/g)]
    .map((match) => match[1].trim().split(/\s+/).length)
    .reduce((sum, words) => sum + words, 0);
  assert.equal(quotedWords, 21);
});

test("text contrast is at least 4.5:1 and control boundaries at least 3:1", () => {
  const colors = Object.fromEntries(
    [...html.matchAll(/--([\w-]+):\s*(#[0-9a-fA-F]{6})\s*;/g)].map((match) => [match[1], match[2]])
  );
  const luminance = (hex) => {
    const channels = hex.slice(1).match(/.{2}/g).map((channel) => parseInt(channel, 16) / 255);
    const linear = channels.map((channel) => channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4);
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
  };
  const contrast = (a, b) => {
    const first = luminance(a);
    const second = luminance(b);
    return (Math.max(first, second) + 0.05) / (Math.min(first, second) + 0.05);
  };
  for (const [foreground, background] of [
    [colors.paper, colors.navy], [colors.paper, colors.panel], [colors.paper, colors["panel-raised"]],
    [colors.muted, colors.navy], [colors.muted, colors.panel], [colors.muted, colors["panel-raised"]],
    [colors.amber, colors.navy], [colors.amber, colors["panel-raised"]], [colors.ink, colors.amber],
    [colors.red, colors["panel-raised"]], [colors.focus, colors.navy], [colors.focus, colors.panel]
  ]) assert.ok(contrast(foreground, background) >= 4.5, foreground + " on " + background + " is below 4.5:1");
  for (const background of [colors.navy, colors.panel, colors["panel-raised"]]) {
    assert.ok(contrast(colors.line, background) >= 3, colors.line + " border on " + background + " is below 3:1");
  }
  const disabledRule = html.match(/\.button:disabled\s*\{([^}]+)\}/);
  assert.ok(disabledRule, "disabled button style exists");
  assert.doesNotMatch(disabledRule[1], /opacity\s*:/, "disabled button opacity must not lower text contrast");
  assert.ok(contrast(colors.paper, "#27384e") >= 4.5, "disabled button text is below 4.5:1");
});

test("the page cites all six source passages with internal locators", () => {
  for (const id of ["S1", "S2", "S3", "S4", "S5", "S6"]) {
    assert.match(html, new RegExp('id="source-' + id + '"'));
    assert.match(html, new RegExp('href="#source-' + id + '"'));
  }
  assert.match(html, /previous 72 ms data cycle/);
  assert.match(html, /0\.05 s active-unit interval/);
  assert.match(html, /separate statements/);
});

test("Ariane 5 is gated behind the Ariane 4 result and changed choices invalidate results", () => {
  assert.ok(html.indexOf('id="fly-a4"') < html.indexOf('id="fly-a5"'));
  assert.match(html, /!state\.results\.A4/);
  assert.match(html, /state\.results = \{ A4: null, A5: null \}/);
  assert.match(html, /Protection choices changed\. Ariane 4 must be run again before Ariane 5\./);
});

test("reduced-motion users skip the playback animation", () => {
  assert.match(html, /prefers-reduced-motion: reduce/);
  assert.match(html, /if \(reducedMotion\)[\s\S]*?setTimeline\(40\);[\s\S]*?finishFlight\(profile, result, token\)/);
});

test("the page has no remote code, stylesheets, images, or analytics requests", () => {
  assert.doesNotMatch(html, /<script\s+[^>]*src=/i);
  assert.doesNotMatch(html, /<link\s+[^>]*rel=["']stylesheet/i);
  assert.doesNotMatch(html, /<img\s+[^>]*src=/i);
  assert.doesNotMatch(html, /\b(fetch|XMLHttpRequest|sendBeacon|gtag|analytics)\s*\(/i);
});


test("initial choice is undecided, 62% load and alignment on", () => {
  assert.equal(model.INITIAL_CHOICE.protected.length, 0);
  assert.equal(model.modelLoad(model.INITIAL_CHOICE.protected), 62);
  assert.equal(model.INITIAL_CHOICE.alignAfterLiftoff, true);
  assert.match(html, /protected: new Set\(INITIAL_CHOICE.protected\)/);
  assert.match(html, /Load the as-flown choice/);
});

test("choose screen does not disclose the historical choice or recommendation", () => {
  const choose = html.slice(html.indexOf('id="choose"'), html.indexOf('<div class="right-rail">'));
  assert.doesNotMatch(choose, /three of the variables|remained unprotected|no purpose|Turn it off/i);
  assert.match(choose, /late countdown hold/);
  assert.match(choose, /href="#source-S6"/);
});

test("both surviving choices provide distinct reasons in the rendered outcome", () => {
  assert.match(model.survivalReason({ ...asFlown, alignAfterLiftoff: false }, "A5"), /Alignment stopped at lift-off/);
  assert.match(model.survivalReason({ protected: ["A", "B", "C", "BH"], alignAfterLiftoff: true }, "A5"), /BH reached 310%.*protected conversion/);
  assert.match(html, /reason.textContent = survivalReason\(currentState\(\), profile\)/);
  assert.match(html, /resultCopy.append\(reason\)/);
});

test("only the BH-with-alignment overflow shows the historical caption", () => {
  const out = html.slice(html.indexOf("function showOutcome"), html.indexOf("function profileName"));
  const historical = out.indexOf("This choice leaves BH unprotected");
  const branch = out.indexOf('if (result.failure.var === "BH" && state.alignAfterLiftoff) {');
  assert.ok(branch > 0 && historical > branch, "historical caption is inside the BH/alignment branch");
  assert.equal(out.split("This choice leaves BH unprotected").length - 1, 1);
  assert.match(out, /"Variable " \+ result\.failure\.var \+ " is unprotected/);
  const aUnprotected = model.simulate({ protected: ["B", "C", "E"], alignAfterLiftoff: true }, "A5");
  assert.equal(aUnprotected.ok, false);
  assert.notEqual(aUnprotected.failure.var, "BH");
});

test("the reveal states the four/three count once", () => {
  const reveal = html.slice(html.indexOf('id="reveal"'), html.indexOf('id="try-again"'));
  assert.equal((reveal.match(/four of the variables|four protected/g) || []).length, 1);
  assert.equal((reveal.match(/three of the variables|three unprotected/g) || []).length, 1);
});
