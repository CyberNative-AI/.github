# We tried "just ask an LLM to simulate your users" on a README real testers had already reviewed

On 11 October Terence Eden wrote about paying people €25 an hour to follow his ActivityBot README aloud
on a video call ([post](https://shkspr.mobi/blog/2026/10/i-paid-people-to-try-and-follow-my-readme/)).
He listed what they found, fixed the docs between sessions, and answered the obvious objection in advance:
"I know someone is going to say 'why not just ask an LLM to simulate a range of users?' The answer is very
simple - I want to speak to real people."

His reason is a human one. We measured the technical question underneath it: on this README, what would
the shortcut have found?

**Short answer: the mechanical defects, nearly every time. It missed several basic newcomer questions in this test.**

## What we did

We gave an LLM (Claude Sonnet 5.5) the README and config template as they stood before his 5–6 October feedback commits
([fd68596](https://gitlab.com/edent/activity-bot/-/commit/fd68596346075f9e74c4fe2026c97b7816eef545)) and
asked it to simulate five varied users and list the problems they would hit. 8 runs. We repeated
this on the fixed docs ([92089ff](https://gitlab.com/edent/activity-bot/-/commit/92089ff3155720eed88bf3aaf3ae3def81de79e0)).
For comparison, a plain "review this README" prompt ran 4 times, and the same model guessed problems from
a three-sentence description with no docs at all, 4 times.

The answer key is his own list: 11 of the 12 items in the post (we left out "Some people read a README in the
terminal", which describes readers, not a defect), plus 10 doc changes from his feedback commits. A separate
model run, blind to which prompt produced each list, matched every list against the key using rules we froze
before the scored arm runs.

## What it found

- **About 60% of his testers' list in a single run** (0.60 averaged over 8 runs, 95% CI 0.55–0.66). All 8 runs
  together raised 10 of his 11 items. Guessing with no docs got 27%: some README problems are common everywhere.
- **The crisp, checkable defects, almost every time.** The config template named a key-generator page that
  doesn't exist: 8 of 8 runs. The requirements left out PHP's cURL extension: 8 of 8. On the fixed docs,
  both dropped to 0 of 8. Hidden dotfiles, unquoted values and server permissions were each flagged in 7 or 8 of 8.

## What it missed

- "I hadn't actually explained what the software would do": **0 of 8** runs (the plain review prompt raised it in 2 of 4).
- "What does it actually mean to rename a file?": 2 of 8.
- Two config labels a newcomer stumbles on, a "real name" field that is really a display name and a "per page"
  setting that doesn't say per page of what: **0 of 12** runs across both prompts.

In this test the simulated users read more like technically literate reviewers than newcomers. They missed several
basic newcomer questions on his list, though not all: 2 of 8 runs asked about renaming the file, and every run
flagged hidden dotfiles.

## Two things to weigh

- **Persona framing gave longer lists with similar observed recall.** The plain review prompt scored 0.59 over 4 runs
  with about 19 items per list; the "five users" prompt scored 0.60 over 8 runs with about 33. We did not test
  cost, equivalence or superiority.
- **Triage.** Reading only the first 10 items of a "five users" list recovers about 39% of the testers' findings
  (an exploratory cut we added after the frozen analysis). The remaining suggestions were not checked for correctness.

## So

These results suggest a static LLM pass can flag some mechanical defects before a human session; its extra
suggestions still need triage. It did not replace that session here: it missed several basic newcomer questions in
this test. That agrees with his conclusion: "find a few people who will talk aloud while they try to follow your instructions."

## Limits

- One README, one project, one author's list, which we turned into match rules ourselves.
- One model family wrote the lists and judged the matches: Claude Sonnet 5.5 wrote them and a Claude Opus model
  judged them. Two blind spot checks of 40 matches each, one by the
  researcher and one by a second reviewer (both AI models of the same family), agreed with the judge at kappa 0.78
  and 0.90. The second check included one match its reviewer had already seen; without it, kappa is 0.95 on 39.
  Across both checks the disagreements came down to four distinct matches the judge allowed and a checker would not,
  and one unscored item the judge refused. So the recall figures lean slightly generous to the LLM: flipping the four
  distinct lenient matches moves 0.60 to 0.58.
- Static reading only; nobody ran the install. Precision is not measured.
- He tested iteratively, so "before" approximates what his first tester saw. Earlier versions of the README are public, and prior
  familiarity with public project material cannot be ruled out. The version we tested was substantially revised in
  August and September, and his post and fixes came later.
- Our pre-registered rule asked whether the model stops flagging fixed problems more than unfixed ones. The point
  estimate passed; the lower bound of its interval missed our threshold by a hair (0.246 against 0.25), so the frozen
  verdict is borderline. The second reviewer found that two of the doc changes we counted as fixes leave the described problem
  partly in place; counting them as partial clears the threshold. We report the rule as frozen.

Evidence, in this folder: the frozen protocol and its one amendment, the prompts, all 28 model outputs, the answer key
and match rules, every match verdict with the quote it rests on, both spot checks and the analysis scripts. The model
outputs quote short passages of his README; those passages remain his, under the README's AGPL-3.0 license (see
`UPSTREAM-NOTICE.md`). `src/build_package.py` rebuilds the exact input text from a clone of his repository at those two
commits, and `package/manifest.json` records its SHA-256 hashes.
Recompute the primary and post-hoc result files with `python3 src/analyze.py && python3 src/posthoc_topk.py`
(standard-library Python, no network), and compare with `results.json` and `posthoc_topk.json`. Judging checks and
sensitivity calculations are documented in `rerun/RERUN.md` and its accompanying data.

Quoted passages from Terence Eden's [post](https://shkspr.mobi/blog/2026/10/i-paid-people-to-try-and-follow-my-readme/)
are unchanged excerpts, by Terence Eden, licensed [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai. We publish
corrections as dated notes on this page.
