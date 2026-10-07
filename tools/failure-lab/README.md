# Failure Lab: quickstart for a 25-minute team session

Failure Lab turns an engineering incident into decisions your team makes together. The group picks what the engineers picked and runs a simplified model on those choices. Then it compares the result with the official inquiry or regulatory record, line by line.

It needs no preparation, accounts or installs. Start a group session [in your browser](https://cybernative.ai/labs/failure-lab/#ariane), or download the files below to run it without network access.

## Run it

**In your browser.** Open [Failure Lab on cybernative.ai](https://cybernative.ai/labs/failure-lab/#ariane), read the Ariane briefing and choose **Start decision 1**. The page also links to the Knight group session and the solo scenarios. Runs in your browser. No hosted session service: the static page loads the lab files, then the group's choices and tallies stay in that page, and reloading clears them.

**One file per scenario.** Download [Ariane](https://raw.githubusercontent.com/CyberNative-AI/.github/main/tools/failure-lab/dist-single/ariane.html) or [Knight](https://raw.githubusercontent.com/CyberNative-AI/.github/main/tools/failure-lab/dist-single/knight.html), save the HTML file, and open it in your browser. Each includes solo and group mode; no other files are needed. [GitLab](https://raw.githubusercontent.com/CyberNative-AI/.github/main/tools/failure-lab/dist-single/gitlab.html) is solo only.

**The whole lab.** [Download Failure Lab](https://raw.githubusercontent.com/CyberNative-AI/.github/main/tools/failure-lab/failure-lab.zip), then extract the folder. Keep the files together so the local links work. The steps below use the whole lab.

1. Open `index.html` in a current browser (Chrome, Edge, Firefox or Safari). Double-clicking the file works; you need no server.
2. Choose **Run with a group**. You can also use the **Run with a group** link on a scenario card to skip the picker.
3. Pick a discussion-timer length (1–4 minutes per decision), then **Start** a scenario:
   - **Ariane 5 Flight 501 (1996).** 2 decisions. Record: the ESA/CNES Inquiry Board report.
   - **Knight Capital, 1 August 2012.** 3 decisions before the market open and 1 during it. Record: the SEC order, Release No. 34-70694.
4. Put the browser in full screen (F11, or Ctrl+Cmd+F on a Mac). The layout uses 24px body type from 1024px wide and 28px on large displays.

The whole session works from the keyboard. Tab moves between controls, Enter or Space presses a button, and Space selects a choice.

## Suggested 25-minute agenda

| Minutes | What happens | On screen |
|---|---|---|
| 0–3 | Read the briefing aloud: role, constraints, evidence. | Brief |
| 3–13 | For each decision, read the prompt, discuss the question (start the timer if you want one), take a show of hands, and record the group's choice. | Decision 1…n |
| 13–15 | Run the model on the group's choices. Knight adds one more decision during the incident. | Run |
| 15–23 | Compare the group's choices with the record, then work through 3–5 discussion questions. Each question cites the numbered source behind it. | Debrief |
| 23–25 | Open the one-page summary, write the team's actions on it, and print it or save it as a PDF. | Summary |

**At each decision:**
- The timer is optional. You can start, pause, resume, reset or skip it, and **Use the timer** brings it back after a skip.
- The show of hands is optional too. If you record one, enter a whole number for every option (0 is fine). Empty, negative or fractional counts are refused with a message.
- **← Back** reopens the previous decision so the group can change its mind.

## What you get at the end

- **Debrief screen:** the group's choice and hand count next to the historical choice for every decision. It also shows the group's modelled outcome beside what actually happened, the discussion questions, and the source register.
- **One-page summary:** scenario, date, decisions (group against record, with tallies, source tags, and a "model equivalent" mark where the option is the model's stand-in for the historical choice), the modelled outcome (model statements only), what actually happened (cited), sourced lessons, blank lines for actions, and sources. The discussion questions stay on the debrief screen. Use **Print or save as PDF**. The page is sized for a single Letter or A4 sheet.

The downloaded files store and send nothing: no cookies, no storage, no analytics and no network requests. In the browser version, the session also stays in the page. Reloading clears the session.

## Honest limits

- **The models are illustrative.** Each one is simplified to isolate the decision under discussion. Costs, peaks, order counts, timings, option bundles and counterfactual outcomes are invented for teaching and are labelled that way. Only statements tagged with a source (S1, S2, …) are historical, and they cite the official record.
- **A modelled "no failure" is not a prediction.** It does not mean the real system would have succeeded.
- **The Ariane plans are simplified.** Group mode offers four protection plans as illustrative bundles of the model's choices; the solo page lets you protect any combination.
- **This is not a certification and makes no training claim.** Nothing here measures what participants learn or how they perform afterwards.
- **Matching the record is not the goal.** The debrief asks why the engineers chose what they did under their constraints, and where your own systems carry the same risk.

## Files

| File | Role |
|---|---|
| `index.html` | Front page: scenarios and the **Run with a group** entry. |
| `ariane501.html`, `knight2012.html` | Solo scenarios, unchanged by facilitator mode. |
| `gitlab2017.html` | Solo GitLab 2017 scenario. It has no group mode yet. |
| `group.html` | Facilitator mode: projector layout, timer, tally, debrief, summary. |
| `group-core.js` | Session state: decisions, tally validation, debrief and summary data. No DOM, storage or network. |
| `group-ariane.js`, `group-knight.js` | Group scenarios. Each holds a byte-for-byte copy of its page's model, plus prompts, record notes, questions and lessons, all tied to that page's source register. |
| `group.test.mjs` | Node tests for the facilitator state, sourcing, model custody and the no-network boundary. |
| `dist-single/ariane.html`, `dist-single/knight.html`, `dist-single/gitlab.html` | One self-contained file per scenario, built from the files above. Ariane and Knight include solo and group mode; GitLab is solo only. |

To run the included checks, use Node's built-in test runner: `node --test test.mjs knight.test.mjs group.test.mjs`. The browser application itself does not require Node.

**Adding a scenario to group mode.** Write a `group-<id>.js` that copies the page's `MODEL-START…MODEL-END` block exactly and calls `FailureLabGroup.register({...})`; `group-knight.js` is the template. Then add one script tag at the `GROUP-SCENARIOS` marker in `group.html`. `register()` refuses any question, lesson or record note without a known source.

Original software and documentation are MIT licensed; see [LICENSE](LICENSE). Included third-party excerpts and linked historical records are outside that grant and remain subject to their respective rights. Prepared with AI assistance. Published by CyberNative AI LLC. Corrections: hello@cybernative.ai. See [NOTICE.txt](NOTICE.txt).
