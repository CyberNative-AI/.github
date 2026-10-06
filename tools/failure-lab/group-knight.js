/* Failure Lab group mode: Knight Capital, 1 August 2012.
   The block between MODEL-START and MODEL-END is a byte-for-byte copy of knight2012.html's model;
   group.test.mjs fails if they drift. Sources S1–S6 are the page's register (sources-knight.md). */
(function () {
  "use strict";
    /* MODEL-START */
    const MODEL_TIMES = [
      { minute: 0, time: "9:30 a.m." },
      { minute: 1, time: "9:31 a.m." },
      { minute: 5, time: "9:35 a.m." },
      { minute: 15, time: "9:45 a.m." },
      { minute: 30, time: "10:00 a.m." },
      { minute: 45, time: "10:15 a.m." }
    ];

    function simulate(state) {
      const vulnerable =
        state.deployment === "manual" &&
        state.featureFlag === "reuse" &&
        state.deadCode === "leave";
      const response = state.response || "continue";
      const halted = vulnerable && response === "halt";
      const rolledBack = vulnerable && response === "rollback";
      const serversRunningFault = !vulnerable || halted ? 0 : (rolledBack ? 8 : 1);
      const cause = vulnerable
        ? {
            server: 8,
            source: ["S2", "S3"],
            description: "The eighth server kept callable Power Peg code; the reused flag activated it, and moved fill tracking did not stop repeated child orders."
          }
        : null;
      const timeline = MODEL_TIMES.map((point) => ({
        minute: point.minute,
        time: point.time,
        orderCount: serversRunningFault * (point.minute + 1),
        serversRunningFault,
        response
      }));

      return {
        ok: !vulnerable || halted,
        timeline,
        cause
      };
    }

    function rollbackComparison(rollbackResult, continuedResult) {
      const rollbackPoint = rollbackResult.timeline.at(-1);
      const continuedPoint = continuedResult.timeline.at(-1);
      return `Without the rollback, this model reaches ${continuedPoint.orderCount} units by ${continuedPoint.time}; with it, ${rollbackPoint.orderCount} (illustrative model units).`;
    }
    /* MODEL-END */

  function modelState(choices) {
    return {
      deployment: choices.deployment,
      featureFlag: choices.featureFlag,
      deadCode: choices.deadCode,
      response: choices.response
    };
  }

  function vulnerable(choices) {
    return simulate(modelState({ deployment: choices.deployment, featureFlag: choices.featureFlag, deadCode: choices.deadCode })).cause !== null;
  }

  /* stage "open": just after the three release decisions. stage "final": after every decision.
     Model statements only in title/text; sourced history goes in `record`, never in the modelled block. */
  function run(choices, stage) {
    const setup = modelState(choices);
    const result = simulate(setup);
    if (result.cause === null) {
      return {
        ok: true,
        title: "No repeated-order failure in this model",
        text: "At least one of the deployment, flag or unused-code choices breaks the modelled chain. The model counter stays at 0 through 10:15 a.m. This is a counterfactual simulation, not a claim about what would have happened.",
        sources: [],
        counter: "0",
        record: null
      };
    }
    if (stage === "open" || !choices.response) {
      const first = result.timeline[1];
      return {
        ok: false,
        title: "9:30 a.m.: the eighth server starts repeating child orders",
        text: "In this model one server missed the new code, the reused flag switches on the old code there, and nothing stops it repeating child orders. By " + first.time + " the model counter reads " + first.orderCount + " (illustrative units). The group has to respond.",
        sources: [],
        counter: String(first.orderCount),
        record: null
      };
    }
    const end = result.timeline[result.timeline.length - 1];
    if (choices.response === "halt") {
      return {
        ok: true,
        title: "The halt stops further accumulation",
        text: "The missed-server cause remains in this setup, but this model sets the repeated-order counter to zero after the router is halted. The model does not claim a historical or counterfactual firm outcome.",
        sources: [],
        counter: String(end.orderCount),
        record: null
      };
    }
    const continued = simulate(Object.assign({}, setup, { response: "continue" }));
    return {
      ok: false,
      title: "The rollback widens the modelled fault to eight servers",
      text: "In this model the rollback returns all eight servers to the old code with the reused flag still on. " + rollbackComparison(result, continued),
      sources: [],
      counter: String(end.orderCount),
      record: {
        title: "What the SEC order says about the rollback",
        steps: [{ time: "", text: "Removing the new code from the seven correct servers caused additional parent orders to activate Power Peg on those servers too.", sources: ["S5"] }]
      }
    };
  }

  FailureLabGroup.register({
    id: "knight",
    title: "Knight Capital, 1 August",
    year: 2012,
    page: "knight2012.html",
    record: "U.S. SEC order, Exchange Act Release No. 70694, 16 October 2013",
    minutes: "3 decisions before the open, 1 during it",
    brief: {
      role: "You are preparing a change to the SMARS order router that has to be live before a busy market open.",
      points: [
        { text: "The change adds new code for a retail liquidity programme to the router, which runs on eight servers.", sources: ["S2"] },
        { text: "Older Power Peg code is no longer used but is still in the router.", sources: ["S2"] },
        { text: "The market opens at 9:30 a.m. You choose how the code ships, how it is switched on, and what happens to old code.", sources: ["S1", "S2"] }
      ],
      note: "Effort estimates, order counts and animation pace are illustrative model values."
    },
    decisions: [
      {
        id: "deployment",
        phase: "before",
        title: "Deployment",
        prompt: "How does the new code reach all eight servers?",
        discuss: "The open is fixed. What would make you confident every server runs the new version?",
        options: [
          { value: "manual", short: "Manual", label: "Copy to each server manually", detail: "One server at a time. Illustrative effort: 10 minutes, one technician." },
          { value: "verified", short: "Verified", label: "Automated deploy with per-server verification", detail: "Confirm every server has the expected version. Illustrative effort: 30 minutes." }
        ],
        recordValue: "manual",
        recordModelEquivalent: true,
        recordNote: { text: "One technician did not copy the new code to one of the eight servers; no second technician reviewed the deployment and no written procedure required it. Manual copy is the model's equivalent.", sources: ["S2"] }
      },
      {
        id: "featureFlag",
        phase: "before",
        title: "Feature flag",
        prompt: "How is the new behaviour switched on?",
        discuss: "Reusing a switch keeps the change small. What else might that switch still control?",
        options: [
          { value: "reuse", short: "Reuse", label: "Reuse an existing flag", detail: "Keep the change small with a switch already in the router." },
          { value: "new", short: "New flag", label: "Add a new flag", detail: "Give the new behaviour its own switch. Illustrative effort: medium." }
        ],
        recordValue: "reuse",
        recordNote: { text: "The new code reused a flag that had previously activated the Power Peg code.", sources: ["S2"] }
      },
      {
        id: "deadCode",
        phase: "before",
        title: "Unused code",
        prompt: "What happens to code this release no longer needs?",
        discuss: "Removing old code before a deadline adds risk too. Which risk do you take?",
        options: [
          { value: "leave", short: "Leave", label: "Leave it in place", detail: "Do not change code outside this release." },
          { value: "remove", short: "Remove", label: "Remove it before release", detail: "Delete the unused path and test the new behaviour." }
        ],
        recordValue: "leave",
        recordNote: { text: "Power Peg was no longer used but remained present and callable.", sources: ["S2"] }
      },
      {
        id: "response",
        phase: "after",
        title: "Response at the open",
        prompt: "Orders are repeating after the open. What do you do?",
        discuss: "You do not yet know the cause. Which action is safer when the fault is unknown?",
        context: { text: "The order does not say that a specific kill-switch device existed.", sources: ["S6"] },
        when: vulnerable,
        notReachedNote: "Not reached: the group's release avoided the modelled incident.",
        options: [
          { value: "rollback", short: "Roll back", label: "Roll back the new code", detail: "Return servers to the prior version." },
          { value: "halt", short: "Halt", label: "Halt SMARS from sending orders", detail: "Stop the router while the issue is assessed." }
        ],
        recordValue: "rollback",
        recordNote: { text: "Knight removed the new code from the seven servers that had it; the order says this caused additional parent orders to activate Power Peg on those servers too.", sources: ["S5"] }
      }
    ],
    run: run,
    history: {
      title: "About 45 minutes, over 4 million executions, over $460 million lost",
      titleSources: ["S1"],
      items: [
        { text: "One of eight servers missed the new code. The reused flag woke the retained Power Peg code there, and moved fill tracking let it repeat child orders without regard to executions already received.", sources: ["S2", "S3"] },
        { text: "97 automated e-mails referencing SMARS and Power Peg arrived before the open. They were not designed as system alerts and generally were not reviewed.", sources: ["S4"] },
        { text: "Removing the new code from the seven correct servers made the incident worse.", sources: ["S5"] },
        { text: "212 parent orders produced over 4 million executions in 154 stocks in about 45 minutes; Knight lost more than $460 million.", sources: ["S1"] }
      ]
    },
    questions: [
      { text: "One technician missed one of eight servers, and no second review or written procedure caught it. How do we confirm every target runs the version we think it runs?", sources: ["S2", "S6"] },
      { text: "A reused flag woke code nobody used but nobody had removed. What dormant code or recycled switches are live in our systems?", sources: ["S2", "S3"] },
      { text: "97 automated e-mails named the problem before the open and were not read as alerts. Which of our automated messages would we ignore?", sources: ["S4"] },
      { text: "Removing the new code from the correct servers made the incident worse. When is rollback our reflex, and how would we know it is the wrong move?", sources: ["S5"] },
      { text: "The order found no procedure to halt the router in response to its own aberrant activity. Who here can stop a misbehaving system, and how fast?", sources: ["S6"] }
    ],
    lessons: [
      { text: "Verify every deployment target; one missed server was enough.", sources: ["S2"] },
      { text: "Remove dead code and never reuse a flag that once switched on something else.", sources: ["S2", "S3"] },
      { text: "Have a written way to halt a system that is misbehaving; rollback can widen an unknown fault.", sources: ["S5", "S6"] }
    ],
    sourceNote: "S1–S6 refer to the SEC order In the Matter of Knight Capital Americas LLC, Release No. 34-70694, §III.",
    sources: {
      S1: "§III, ¶1. Date, about 45 minutes, executions, shares, positions, loss greater than $460 million.",
      S2: "§III, ¶¶12–13, 15–16. New code, retained Power Peg code, reused flag, one of eight servers missed.",
      S3: "§III, ¶¶14, 16. Moved cumulative-share tracking; repeated child orders.",
      S4: "§III, ¶19. 97 automated pre-open e-mails, generally not reviewed.",
      S5: "§III, ¶27. Removing the new code from seven servers worsened the incident.",
      S6: "§III, ¶¶21, 26–27. Deployment, unused-code, halt and incident-response controls."
    }
  });
}());
