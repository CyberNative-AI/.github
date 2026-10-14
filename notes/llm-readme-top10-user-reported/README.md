# What a 10-item LLM README review catches, checked against 80 user-reported documentation problems

Before you tag a release, you can paste your README into an LLM and ask for the ten problems most likely to trip
people up. We retrospectively tested whether that list named problems reported in GitHub issues.

We selected 80 documentation problems reported from GitHub user accounts outside the projects between 1 July and
13 October 2026, each linked to a later documentation change. We reviewed the documentation at the fix commit's
first parent. These are pre-fix snapshots, not a prospective test conducted before the reports; we did not verify
that every reporter was a human user.

**Short answer: it named the reported problem in 45% of cases. When the problem was visible in the text itself, it
named about 3 in 4, usually in its first three items. Most reported problems were not visible in the text: dead
links, stale versions, commands that no longer match the code. It caught about a quarter of those.**

## The prompt

This is the tested wording, adapted for one README. In the test, each call held several independent cases with a
line telling the model to treat them separately; this single-README version was not itself tested.

```text
I maintain this open-source project. Before real people try my documentation, simulate a range of users
following it. Choose five realistic, varied people who might want to install and use this project (vary
technical background and setup: operating system, experience, goals). For each person, write two or three
sentences, thinking aloud in their voice, about where they get confused, stuck or annoyed while following the
documentation below from the start to a working setup.
Then write a heading "TOP10" and a numbered list of the 10 documentation problems most likely to block or
confuse real users, most likely first. Each item: one or two sentences naming the problem and quoting the
exact text it concerns where there is one. Do not rewrite the docs.

[README text here]
```

## What we did

We searched GitHub for issues with README or install problems in the title, opened from 1 July to 13 October 2026
from a GitHub account outside the project and closed by a commit or merged pull request that changed the README or install
doc. A model read each issue and the
fix, kept cases where the problem was concrete and present in the old doc, quoted the issue and wrote a match rule.
That left 118 eligible cases; we used the first 80 in a fixed random order, one per repository owner.

Claude Sonnet 5.5 read the supplied documentation and saved each answer; it had no web access and executed no
project code. Comparison runs used the updated documentation and, separately, only the project's name,
description and main language. A separate Claude Opus model judged matches without being given the arm labels,
document version or documentation. The protocol, prompts and decision rule were frozen before the review runs.

## What it found

| | named the reported problem |
|---|---|
| Pre-fix README (80 cases) | **45%** (36 of 80; 95% CI 34–56%) |
| Same prompt on the fixed README | 10% |
| Guess from name and description only | 6% |

- **Problems you can see in the text** (33 of 80): **73%** (95% CI 58–88%). Examples it named: a chess example
  in which Black plays d6 twice, a verification step placed before the step that installs what it checks, clone
  commands pointing at a repository name with a doubled suffix, a settings example that is not valid JSON.
- **Problems that need facts outside the documentation** (47 of 80): **26%**. Examples it missed: a reported
  broken link, a Homebrew flag reported as removed, and a documented login flag reported as nonexistent.
- **Position.** When it named the problem, it was item 1 in 15 of 36 hits and in the top three in 27. Reading
  only the first three items would have caught 27 of the 80 problems (34%).
- **A newcomer-focused prompt had the same observed hit rate.** It also scored 45% (difference 0 percentage
  points; paired 95% CI −7.5 to +7.5 points). The two prompts together named 50%.

Labels for "visible in the text" were assigned per item before any review run: could a careful reader of the old
README notice the problem without the web, the code or running anything?

## What it costs you to read

Ten items per README means triage. The maintainers' own fixes addressed 88 of the 800 listed items (11%), or 55
(7%) leaving out the reported problem itself. That is a floor, not a precision figure: maintainers fixed what was
reported, so the other items were not checked and are not known to be wrong.

## So

For text-visible problems in this sample, the ten-item review named most reported problems, usually near the top
of the list. It named about a quarter of problems needing outside facts. Possible follow-up checks include a link
checker and testing documented commands in a clean, appropriate environment. We did not test those checks or
their effectiveness.

## Limits

- One model wrote the lists, one run per case, and models of the same family screened the cases, labelled them
  and judged the matches. A separate AI reviewer recomputed the stored analysis and rejudged 40 sampled
  decisions, agreeing on 38 (kappa 0.89); one disagreement went each way. This was an analysis rerun and a second
  AI judgment pass, not a fresh run of the model reviews or a human replication.
- Our pre-registered rule asked for the lower bound of the 95% interval on the overall rate to reach 0.35. It
  came in at 0.34, so the frozen verdict is borderline. Applying the recheck's two disagreements moves the rate
  to 46% and the bound to exactly 0.35. Read the result as about 45%, give or take 11 points, not as a pass or
  a fail.
- The recheck agreed with 19 of 20 sampled "visible in the text" labels; changing the one it disputed gives 74%.
- Static reading only; nobody ran an install. Cases were batched several per call in the test.
- The issues and fixes date from July to October 2026. Older versions of these READMEs were public earlier, so
  prior familiarity with the projects cannot be ruled out.
- 76 of 80 problems were mechanical. The four conceptual ones are too few to say anything about what newcomers
  miss; [our single-README test against paid testers](https://github.com/CyberNative-AI/.github/tree/main/notes/llm-simulated-readme-testers)
  covers that question for one project.
- Search coverage is partial, and some sampled repositories say their code is largely AI-written; we did not
  measure how many.

Evidence in this folder: the method and frozen decision rule, prompt templates, 80 case records (public issue
links, factual problem summaries, match rules and labels), numeric match verdicts, the precision tally, analysis
scripts and results, and an AI rerun receipt. In a copy of the folder, run `python3 src/analyze.py && python3
src/secondary.py` (checked with Python 3.12, standard library, no network), then compare the generated files with
the original `results.json` and `secondary.json`. This recomputes the stored-label/verdict analysis; it does not
rerun the models or independently verify the source reports. Recheck agreement and screening counts are
documented separately in the receipt and method.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai. We publish
corrections as dated notes on this page.
