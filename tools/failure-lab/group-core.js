/* Failure Lab group mode: session state for a facilitated run.
   Pure functions only: no DOM, no storage, no network. group.html renders them;
   group.test.mjs runs them in Node. Scenario files call FailureLabGroup.register(). */
(function (root) {
  "use strict";

  const scenarios = [];

  function register(def) {
    ["id", "title", "year", "page", "record", "brief", "decisions", "run", "history", "questions", "lessons", "sources"].forEach(function (key) {
      if (def[key] === undefined) throw new Error("Scenario " + (def.id || "?") + " is missing " + key);
    });
    if (def.questions.length < 3 || def.questions.length > 5) throw new Error(def.id + ": 3 to 5 discussion questions");
    const cite = function (item, where) {
      if (!item.sources || !item.sources.length) throw new Error(def.id + ": " + where + " has no source");
      item.sources.forEach(function (id) {
        if (!def.sources[id]) throw new Error(def.id + ": " + where + " cites unknown source " + id);
      });
    };
    def.questions.forEach(function (q, i) { cite(q, "question " + (i + 1)); });
    def.lessons.forEach(function (l, i) { cite(l, "lesson " + (i + 1)); });
    def.history.items.forEach(function (h, i) { cite(h, "history item " + (i + 1)); });
    cite({ sources: def.history.titleSources }, "history title");
    def.decisions.forEach(function (d) {
      cite(d.recordNote, "record for " + d.id);
      if (!d.options.some(function (o) { return o.value === d.recordValue; })) throw new Error(def.id + ": record value missing for " + d.id);
    });
    if (scenarios.some(function (s) { return s.id === def.id; })) throw new Error("Duplicate scenario " + def.id);
    scenarios.push(def);
  }

  function list() { return scenarios.slice(); }

  function get(id) {
    return scenarios.find(function (s) { return s.id === id; }) || null;
  }

  function createSession(scenario) {
    return { scenarioId: scenario.id, choices: {}, tallies: {} };
  }

  function choicesOf(session) { return Object.assign({}, session.choices); }

  function isActive(decision, choices) {
    return !decision.when || decision.when(choices);
  }

  /* The next decision still to record in a phase ("before" the run or "after" it), or null. */
  function nextDecision(scenario, session, phase) {
    const choices = choicesOf(session);
    return scenario.decisions.find(function (d) {
      return (d.phase || "before") === phase && isActive(d, choices) && !(d.id in session.choices);
    }) || null;
  }

  function hasAfterPhase(scenario, session) {
    const choices = choicesOf(session);
    return scenario.decisions.some(function (d) { return d.phase === "after" && isActive(d, choices); });
  }

  /* Tally fields arrive as raw strings. Every option needs a whole number of hands, 0 allowed. */
  function parseTally(decision, raw) {
    const counts = {};
    for (let i = 0; i < decision.options.length; i += 1) {
      const option = decision.options[i];
      const value = String(raw && raw[option.value] !== undefined ? raw[option.value] : "").trim();
      const name = "“" + option.short + "”";
      if (value === "") return { ok: false, field: option.value, error: "Enter the number of hands for " + name + ". Use 0 if nobody chose it." };
      if (/^-/.test(value)) return { ok: false, field: option.value, error: "Hands for " + name + " cannot be negative. Enter 0 or more." };
      if (!/^\d+$/.test(value)) return { ok: false, field: option.value, error: "Hands for " + name + " must be a whole number, like 4." };
      const n = Number(value);
      if (n > 9999) return { ok: false, field: option.value, error: "Hands for " + name + " looks too large. Enter up to 9999." };
      counts[option.value] = n;
    }
    return { ok: true, counts: counts };
  }

  /* Returns a new session. tally is null (skipped) or the counts from parseTally. */
  function recordChoice(scenario, session, decisionId, value, tally) {
    const decision = scenario.decisions.find(function (d) { return d.id === decisionId; });
    if (!decision) throw new Error("Unknown decision " + decisionId);
    if (!decision.options.some(function (o) { return o.value === value; })) throw new Error("Unknown option " + value + " for " + decisionId);
    const choices = Object.assign({}, session.choices);
    const tallies = Object.assign({}, session.tallies);
    choices[decisionId] = value;
    if (tally) tallies[decisionId] = Object.assign({}, tally);
    else delete tallies[decisionId];
    // A changed answer can deactivate later decisions; drop their stale answers.
    scenario.decisions.forEach(function (d) {
      if (d.id !== decisionId && d.id in choices && !isActive(d, choices)) {
        delete choices[d.id];
        delete tallies[d.id];
      }
    });
    return { scenarioId: session.scenarioId, choices: choices, tallies: tallies };
  }

  function optionLabel(decision, value) {
    const option = decision.options.find(function (o) { return o.value === value; });
    return option ? option.label : "";
  }

  function tallyText(decision, tally) {
    if (!tally) return "";
    const total = decision.options.reduce(function (sum, o) { return sum + tally[o.value]; }, 0);
    return decision.options.map(function (o) { return o.short + " " + tally[o.value]; }).join(" · ") + " (" + total + " hands)";
  }

  function isComplete(scenario, session) {
    return !nextDecision(scenario, session, "before") && !nextDecision(scenario, session, "after");
  }

  /* Group choice against the record, one row per decision in scenario order. */
  function debrief(scenario, session) {
    const choices = choicesOf(session);
    const rows = scenario.decisions.map(function (d) {
      const reached = isActive(d, choices) && d.id in choices;
      const chosen = reached ? choices[d.id] : null;
      return {
        id: d.id,
        title: d.title,
        reached: reached,
        notReachedNote: reached ? "" : (d.notReachedNote || "Not reached in this run."),
        chosenValue: chosen,
        chosenLabel: reached ? optionLabel(d, chosen) : "",
        tally: reached && session.tallies[d.id] ? Object.assign({}, session.tallies[d.id]) : null,
        tallyText: reached ? tallyText(d, session.tallies[d.id]) : "",
        recordValue: d.recordValue,
        recordLabel: optionLabel(d, d.recordValue),
        recordNote: d.recordNote,
        recordSources: d.recordNote.sources.slice(),
        recordModelEquivalent: Boolean(d.recordModelEquivalent),
        matchesRecord: reached && chosen === d.recordValue
      };
    });
    return {
      scenario: scenario,
      rows: rows,
      matched: rows.filter(function (r) { return r.matchesRecord; }).length,
      outcome: scenario.run(choices, "final"),
      history: scenario.history,
      questions: scenario.questions
    };
  }

  /* The printable one-page summary, as data. */
  function summary(scenario, session) {
    const d = debrief(scenario, session);
    return {
      heading: "Failure Lab session summary",
      scenario: scenario.title + " (" + scenario.year + ")",
      record: scenario.record,
      decisions: d.rows.map(function (r) {
        return {
          title: r.title,
          group: r.reached ? r.chosenLabel : r.notReachedNote,
          tally: r.tallyText,
          record: r.recordLabel,
          recordModelEquivalent: r.recordModelEquivalent,
          recordSources: r.recordSources,
          matchesRecord: r.matchesRecord
        };
      }),
      // Modelled block: model statements only, no source tags.
      outcome: { title: d.outcome.title, text: d.outcome.text },
      history: { title: scenario.history.title, sources: scenario.history.titleSources.slice(), items: scenario.history.items },
      lessons: scenario.lessons,
      questions: scenario.questions,
      sources: Object.keys(scenario.sources).map(function (id) { return { id: id, text: scenario.sources[id] }; }),
      limits: "Simplified teaching model. Option bundles, costs, counts, timings and counterfactual outcomes are illustrative; historical statements cite the numbered sources. Not a certification or a measure of training effect."
    };
  }

  root.FailureLabGroup = {
    register: register,
    list: list,
    get: get,
    createSession: createSession,
    nextDecision: nextDecision,
    hasAfterPhase: hasAfterPhase,
    parseTally: parseTally,
    recordChoice: recordChoice,
    isComplete: isComplete,
    tallyText: tallyText,
    debrief: debrief,
    summary: summary
  };
}(typeof globalThis !== "undefined" ? globalThis : this));
