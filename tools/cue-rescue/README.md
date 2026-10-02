# Cue Rescue — rehearse a disrupted two-room plan

A local rehearsal prototype for a small event programme with shared resources. Load a plan, introduce a delay or unavailable resource, compare recovery choices, accept one, then export and reopen the revised plan.

This is **not live show control or a staffing guarantee**. Examples are original synthetic scenes. The interface's “Private planning” label means local rehearsal; the code is now available here.

## Download and open

[Download Cue Rescue ZIP](https://raw.githubusercontent.com/CyberNative-AI/.github/refs/heads/main/tools/cue-rescue/cue-rescue.zip). Extract the whole archive into one folder, then open `index.html` in a current desktop browser with JavaScript enabled. Keep `engine.js`, `app.js` and `styles.css` alongside it. GitHub's HTML source view does not run the application. No account, server or package installation is needed.

Start with the included two-room example or import a version1 JSON plan such as `fixtures/two-room.json`. CSV import is not available. Keep private schedules and personal details out of feedback.

## One voluntary task

If this resembles your planning job, try a sanitized two-room plan for up to ten minutes:

1. Record the time needed to enter/import the plan and specify its hard constraints. Use invented labels and remove personal, confidential and customer data.
2. Make one cue late or mark one shared resource unavailable. Inspect conflicts and compare the offered choices.
3. Explicitly accept a choice. Download the revised JSON and printable cue sheet, then import the downloaded JSON to reopen it.
4. Compare the **whole job**, including setup and checking, with the same change in your usual spreadsheet or planning tool.

Optional feedback to hello@cybernative.ai: which steps you completed, setup/repair/export time, your usual method, and the first confusing or unsupported step. Send only synthetic examples or a description; no private event files, credentials or personal data. No signup or feedback is required. We have not established that this is faster or better than your existing workflow.

## Limits that matter

- JSON version1 only; at most12 cues,4 rooms,8 resources and a720-minute window. All times use whole minutes.
- A cue occupies its room and each exclusive resource for its **entire duration**. Partial setup/teardown, travel, precedence and resource capacity greater than one are not modeled.
- The browser examines at most5,000 candidate placements and returns up to3 feasible choices. It may miss feasible or better alternatives; similar one-minute shifts are possible. “None found within budget” does not prove impossibility.
- Locks, minimum durations, cutoffs and rooms remain constraints. Inspect every proposed change before accepting it.
- No live timers, collaboration, automatic persistence, operational safety assurance or staffing promise. Keep the downloaded JSON yourself. Mobile ZIP handling and real event use have not been validated.

The application was created with AI assistance by CyberNative AI LLC. It uses original synthetic examples and no external runtime dependencies. Publisher and corrections: CyberNative AI LLC, hello@cybernative.ai. The included MIT license covers this package, not other repository material or third-party tools. Outside usefulness, learning outcomes and comparative savings remain unestablished.
