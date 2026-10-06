/* Failure Lab group mode: Ariane 5 Flight 501.
   The block between MODEL-START and MODEL-END is a byte-for-byte copy of ariane501.html's model;
   group.test.mjs fails if they drift. Sources S1–S6 are the page's register (sources-ariane.md). */
(function () {
  "use strict";
    /* MODEL-START */
    const MODEL = Object.freeze({
      baseLoad: 62,
      target: 80,
      costs: Object.freeze({ A: 4, B: 3, C: 5, D: 3, E: 4, F: 2, BH: 4 }),
      defaultProtected: Object.freeze(["A", "B", "C", "E"]),
      variables: Object.freeze(["A", "B", "C", "D", "E", "F", "BH"]),
      peaks: Object.freeze({
        A4: Object.freeze({ A: 140, B: 120, C: 130, D: 40, E: 96, F: 30, BH: 60 }),
        A5: Object.freeze({ A: 150, B: 125, C: 135, D: 70, E: 98, F: 50, BH: 310 })
      })
    });

    function modelLoad(protectedVariables) {
      const selected = new Set(protectedVariables || []);
      let load = MODEL.baseLoad;
      MODEL.variables.forEach(function (id) {
        if (selected.has(id)) load += MODEL.costs[id];
      });
      return load;
    }

    function simulate(state, profile) {
      const load = modelLoad(state.protected);
      const overBudget = load > MODEL.target;
      if (overBudget) return { ok: false, load: load, overBudget: true, failure: null };
      const peaks = MODEL.peaks[profile];
      if (!peaks) throw new Error("Unknown profile");
      let failure = null;
      MODEL.variables.some(function (id) {
        if (id === "BH" && !state.alignAfterLiftoff) return false;
        if (!state.protected.includes(id) && peaks[id] > 100) {
          failure = { var: id, tBackup: id === "BH" && profile === "A5" ? 36.7 : null, tActiveApprox: id === "BH" && profile === "A5" ? "~0.05 s later" : null, tBreakup: id === "BH" && profile === "A5" ? 39 : null };
          return true;
        }
        return false;
      });
      return { ok: failure === null, load: load, overBudget: false, failure: failure };
    }
    const INITIAL_CHOICE = Object.freeze({ protected: Object.freeze([]), alignAfterLiftoff: true });

    function survivalReason(choice, profile) {
      if (profile !== "A5") return "";
      if (!choice.alignAfterLiftoff) return "Illustrative: Alignment stopped at lift-off, so BH was not computed in flight.";
      return "Illustrative: BH reached 310% of the limit; the protected conversion did not halt the unit in this model.";
    }
    /* MODEL-END */

  const PLANS = {
    ABCE: ["A", "B", "C", "E"],
    ABCBH: ["A", "B", "C", "BH"],
    ABC: ["A", "B", "C"],
    ALL: MODEL.variables.slice()
  };

  function modelState(choices) {
    return {
      protected: PLANS[choices.protect] || [],
      alignAfterLiftoff: choices.align !== "stop"
    };
  }

  /* Model statements only in title/text; sourced history goes in `record`, never in the modelled block. */
  function run(choices) {
    const state = modelState(choices);
    const a4 = simulate(state, "A4");
    if (a4.overBudget) {
      return {
        ok: false,
        title: "The plan breaks the workload target",
        text: "Protecting all seven conversions puts illustrative processor load at " + a4.load + "%, above the model's 80% target. The lab does not fly an over-budget plan, so neither profile runs.",
        sources: [],
        record: null
      };
    }
    const a5 = simulate(state, "A5");
    if (!a4.ok) {
      return {
        ok: false,
        title: "Ariane 4 reaches an overflow on " + a4.failure.var,
        text: "Variable " + a4.failure.var + " is unprotected and exceeds its limit on the illustrative Ariane 4 profile. This is not a reported Ariane 4 event.",
        sources: [],
        record: null
      };
    }
    if (a5.ok) {
      return {
        ok: true,
        title: "Both profiles avoid the modelled failure",
        text: "Ariane 4 and Ariane 5 both fly without an overflow in this model. " + survivalReason(state, "A5") + " This outcome applies only to the simplified model; it does not predict the full mission outcome.",
        sources: [],
        record: null
      };
    }
    if (a5.failure.var === "BH" && state.alignAfterLiftoff) {
      return {
        ok: false,
        title: "Ariane 5 reaches an overflow on BH",
        text: "Ariane 4 flies without an overflow in this model. On the Ariane 5 profile BH is unprotected while alignment runs; its illustrative peak is 310% of the 16-bit limit, so the conversion overflows and the unit halts in this model.",
        sources: [],
        record: {
          title: "What the Inquiry Board reported for Flight 501",
          steps: [
            { time: "H0 + 36.7 s", text: "The backup unit fails on the BH conversion.", sources: ["S1", "S4"] },
            { time: "About 0.05 s later", text: "The active unit fails the same way. The units used identical hardware and software.", sources: ["S4"] },
            { time: "Next in the report sequence", text: "Diagnostic data is read as flight data. The flight computer commands full nozzle deflections.", sources: ["S4"] },
            { time: "H0 + 39 s", text: "The launcher disintegrates. Automatic destruction follows.", sources: ["S4"] }
          ]
        }
      };
    }
    return {
      ok: false,
      title: "Ariane 5 reaches an overflow on " + a5.failure.var,
      text: "Variable " + a5.failure.var + " is unprotected and exceeds its limit on the illustrative Ariane 5 profile. The report describes no matching Ariane 501 event.",
      sources: [],
      record: null
    };
  }

  FailureLabGroup.register({
    id: "ariane",
    title: "Ariane 5 Flight 501",
    year: 1996,
    page: "ariane501.html",
    record: "ESA/CNES Inquiry Board report, 19 July 1996",
    minutes: "2 decisions",
    brief: {
      role: "You are the 1990s inertial-reference software team for the new Ariane 5 launcher.",
      points: [
        { text: "Seven conversions from 64-bit floating point to signed 16-bit integer could overflow. In this model, an unprotected overflow halts the unit.", sources: ["S1", "S2"] },
        { text: "Protecting a conversion costs processor time, and the workload target is 80%.", sources: ["S2"] },
        { text: "Your evidence is how the same software behaved on Ariane 4 flights.", sources: ["S3"] }
      ],
      note: "Variable labels A–F, costs, peaks and the 62% base load are illustrative model values."
    },
    decisions: [
      {
        id: "protect",
        phase: "before",
        title: "Spend the protection budget",
        prompt: "Which conversions get overflow protection?",
        discuss: "Ariane 4 evidence says which peaks crossed the limit. Is that evidence enough for a new launcher?",
        table: {
          caption: "Ariane 4 peak as % of the 16-bit limit, and protection cost · illustrative",
          head: ["Conversion", "Ariane 4 peak", "Cost"],
          rows: MODEL.variables.map(function (id) {
            return [id === "BH" ? "BH · horizontal bias" : id, MODEL.peaks.A4[id] + "%", "+" + MODEL.costs[id]];
          })
        },
        options: [
          { value: "ABCE", short: "A B C E", label: "Protect A, B, C and E", detail: "The three that crossed the limit on Ariane 4, plus E at 96%. Load 78%." },
          { value: "ABCBH", short: "A B C BH", label: "Protect A, B, C and BH", detail: "Swap E for BH, the alignment value. Load 78%." },
          { value: "ABC", short: "A B C", label: "Protect A, B and C only", detail: "Only what crossed the limit on Ariane 4. Load 74%." },
          { value: "ALL", short: "All seven", label: "Protect all seven", detail: "Every conversion. Load 87%, over the 80% target." }
        ],
        optionNote: "Options are illustrative bundles of the model's choices; the solo page lets you pick any combination.",
        recordValue: "ABCE",
        recordModelEquivalent: true,
        recordNote: { text: "Protection covered four of the seven at-risk variables; three, BH among them, stayed unprotected. A, B, C and E is the model's illustrative mapping of that choice.", sources: ["S2"] }
      },
      {
        id: "align",
        phase: "before",
        title: "Keep alignment running after lift-off",
        prompt: "After lift-off, does the alignment function keep running?",
        discuss: "This behaviour is proven on Ariane 4. What does keeping it buy you, and what does it cost?",
        context: { text: "On Ariane 4, continued alignment allowed a quick restart after a late countdown hold, avoiding launcher events that take hours to reset. It was retained for commonality.", sources: ["S6"] },
        options: [
          { value: "keep", short: "Keep", label: "Keep it running", detail: "Same proven behaviour as Ariane 4." },
          { value: "stop", short: "Stop", label: "Stop it at lift-off", detail: "Change behaviour that worked on Ariane 4." }
        ],
        recordValue: "keep",
        recordNote: { text: "Alignment kept running after lift-off, a requirement retained from Ariane 4 for commonality.", sources: ["S6"] }
      }
    ],
    run: run,
    history: {
      title: "Flight 501 broke up 39 seconds after lift-off",
      titleSources: ["S4"],
      items: [
        { text: "Protection was added to four of the seven at-risk variables; three, BH among them, stayed unprotected. The report found no evidence that Ariane 5 trajectory data were used to analyse them.", sources: ["S2", "S3"] },
        { text: "The backup unit failed at H0 + 36.7 s and the active unit about 0.05 s later, the same way, on identical hardware and software. Diagnostic data was read as flight data; the launcher disintegrated at H0 + 39 s.", sources: ["S4"] },
        { text: "The alignment function had no purpose after lift-off on Ariane 5. The Board's first recommendation was to switch it off immediately after lift-off.", sources: ["S1", "S5"] }
      ]
    },
    questions: [
      { text: "The team judged BH safe from Ariane 4 evidence, and the report found no sign that Ariane 5 trajectory data were used. Which of our safety assumptions were proven on a system we no longer run?", sources: ["S2", "S3"] },
      { text: "Both units failed the same way about 0.05 s apart because they ran identical software. Where does our redundancy share a single failure mode?", sources: ["S4"] },
      { text: "Alignment served no purpose after lift-off but kept running for commonality. What do we keep running only because it worked before?", sources: ["S1", "S6"] },
      { text: "A diagnostic output was read as flight data. Where could an error value in our systems be consumed as a real one?", sources: ["S4"] },
      { text: "An 80% workload target decided what got protected. Which of our budgets decide what we guard, and who sees that trade-off?", sources: ["S2"] }
    ],
    lessons: [
      { text: "Evidence from a previous system is only valid for the conditions it covered; BH was left unprotected on Ariane 4 reasoning.", sources: ["S3"] },
      { text: "Identical redundant units fail identically.", sources: ["S4"] },
      { text: "Behaviour with no purpose in the new context is still a failure path; the Board's first fix was to switch it off.", sources: ["S1", "S5"] }
    ],
    sourceNote: "S1–S6 refer to the ESA/CNES Inquiry Board report, 19 July 1996.",
    sources: {
      S1: "§2.1, PDF p. 5. BH conversion from 64-bit float to signed 16-bit integer caused an Operand Error; alignment served no purpose after lift-off.",
      S2: "§2.2, PDF p. 6. 80% workload target; seven variables at risk; four protected, three (including BH) unprotected.",
      S3: "§2.2, PDF p. 6; §3.1(o), PDF p. 13. Faulty reasoning about BH; no evidence Ariane 5 trajectory data were used.",
      S4: "§3.1(e–j), PDF pp. 11–12; §2.1, PDF p. 5. Backup failed at H0 + 36.7 s, active unit about 0.05 s later; diagnostic data read as flight data; disintegration at H0 + 39 s.",
      S5: "§4, Recommendation 1, PDF p. 14. Switch off alignment immediately after lift-off.",
      S6: "§2.2, PDF p. 7; §3.1(m), PDF p. 12. Continued alignment supported late-hold restart on Ariane 4; retained for commonality."
    }
  });
}());
