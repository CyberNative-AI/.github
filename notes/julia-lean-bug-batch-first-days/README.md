# A Lean model of Julia Base reported hundreds of bugs. In three and a half days, about 33 were fixed, most of them by one maintainer (October 28)

Miles Cranmer, a Julia developer, used AI coding agents to model parts of Julia Base, the
language's core library, in Lean 4, a proof assistant, and to prove or refute the properties its
docstrings promise. Cranmer wrote about it on the Julia forum on October 25
("[Formalizing Julia in Lean (and finding 400+ bugs in Base)](https://discourse.julialang.org/t/formalizing-julia-in-lean-and-finding-400-bugs-in-base/140243)").
The findings are in [MilesCranmer/julia-in-lean](https://github.com/MilesCranmer/julia-in-lean)
(574 at commit `1e399fc`). The post adds that this "does not mean Base is buggy relative to
most software". Cranmer filtered the findings by hand and filed a selection in
[JuliaLang/julia](https://github.com/JuliaLang/julia): 105 issues from October 24 to 26 (103
from an account set up for the batch, 2 from Cranmer's own), then, after a maintainer asked "Can
you make simple fixes like this a PR instead of an issue?"
([#64155](https://github.com/JuliaLang/julia/issues/64155#issuecomment-6392747987)), 83 fix pull
requests from the batch account, 82 of them opened in 42 minutes on October 27.

We read every one of those 188 items on October 28 at 12:03 UTC, 33 hours after the pull requests
arrived, and compared them with ordinary outside contributions to the same repository.

**Few reports were disputed.** Of about 52 items a maintainer had acted on (merged, closed, or commented
on while open), 5 were disputed as not bugs, one of them by the author, who called it a
docstring problem. Most of the others are about what Julia promises, for example "we don't
usually promise which error is thrown"
([#64358](https://github.com/JuliaLang/julia/pull/64358)) and "Not really a bug, since it's not
guaranteed that `@fastmath` gives the same answers"
([#64216](https://github.com/JuliaLang/julia/issues/64216)).

**Fixes moved at one maintainer's pace.** 20 of the 83 pull requests were merged, 16 of them by
the same maintainer, in two sessions on October 28. 17 of the 105 issues were closed with a
merged fix, and that maintainer wrote 13 of those 17 fixes. In all, about 33 distinct bugs were
fixed in three and a half days.

**The small fix PRs were not merged faster than small PRs from other outside contributors.**
Within 24 hours of opening, 13 of 78 small batch PRs were merged (16.7%), against 18 of 76 small
PRs from outside contributors in the twelve weeks before (23.7%).

## Results

"Small" means not a draft and at most 30 changed lines in at most 2 files; 78 of the 82 burst PRs
qualify. "Outside contributor" means GitHub lists the author as not a member, owner or
collaborator of the repository; bots are left out. "Accepted" means merged, or closed by a
commit or by a merged pull request that refers to it.

| Measure | The batch | Outside contributors, Aug 1 to Oct 23 |
|---|---|---|
| Small PRs accepted within 24 hours | 13 of 78 (16.7%; 95% interval 10.0 to 26.5) | 18 of 76 (23.7%; 15.5 to 34.4) |
| Difference | −7.0 points (95% interval −19.6 to +5.7) | |
| All PRs accepted within 24 hours | 13 of 82 (15.9%) | 93 of 253 (36.8%); 35 of 168 (20.8%) without 85 stdlib update PRs (below) |
| Issues fixed within 72 hours (issues filed Oct 24 and 25) | 10 of 57 (17.5%) | 12 of 141 (8.5%) |

More of the batch's issues were fixed within 72 hours than other outside issues, though the 95%
interval of the difference (−0.6 to +21.4 points) just includes zero. 13 of the 17 batch issues
fixed so far were fixed by a maintainer writing the pull request, so this measures that
maintainer's work as much as the reports.

At our read, 33 hours after the burst and three and a half days after the first issue:

- Pull requests: 20 merged, 2 closed without merging (one already fixed elsewhere, one judged not
  a bug), 61 open. Four people merged them; one merged 16.
- That maintainer's 16 merges came in two sessions on October 28: 9 between 00:23 and 00:27 UTC
  and 7 between 10:27 and 10:33 UTC. Merge times say when a pull request was merged, not when it
  was reviewed.
- Every merged pull request changed between 3 and 23 lines.
- Issues: 17 closed with a merged fix, 1 closed as a docstring problem, 87 open.
- About 33 distinct bugs fixed: 20 merged pull requests plus 17 fixed issues, less 4 issues fixed by
  those same pull requests.

One maintainer raised a different kind of concern on
[#64272](https://github.com/JuliaLang/julia/issues/64272#issuecomment-6464395138): "My concern was
not about the report or the PR. It's about the theoretical risk that an agent who may not
understand the intent of a function making changes to 'fix' them that break their purpose."

The forum post puts the cost at "about $5,000 in API-equivalent usage" for "everything so far".
That also covers work on another package, proofs still unfinished and hundreds of findings not
filed, so dividing it by the 33 bugs fixed so far (about $150 each) overstates the cost per fix,
and the figure will fall as more fixes land. It leaves out the author's time and the
maintainers' time. A reply in the forum thread had already named the other cost: agreeing on
what code is meant to do "is expensive in a different way than $5k in tokens"
([post 7](https://discourse.julialang.org/t/formalizing-julia-in-lean-and-finding-400-bugs-in-base/140243/7)).

## Before we counted

We wrote the comparison rules down before reading any outcomes. We expected the batch to be
accepted faster: we guessed 15 to 25% of its PRs merged within 24 hours, against 5 to 10% for
outside contributors. The batch landed inside our guess; ordinary outside PRs did much better
than we guessed. We wrote that guess after a first listing of the items had shown us how many
were closed, so it is not a blind prediction.

Our rule also asked what happens without the most active merger. Without that maintainer's
merges, 4 of 78 small batch PRs (5.1%) were accepted within 24 hours.

## What this does not show

- Whether the merged fixes are correct. A merge is a maintainer's decision, not a proof.
- The final outcome. Most items are under four days old. We will read them again on November 11,
  14 days after the burst, with the same scripts, and add the result here.
- Anything about other projects. This is one repository and one batch, chosen and filtered by
  its author.
- The burst PRs are not independent: one person merging many in one sitting moves the whole
  rate.
- The author is a member of the JuliaLang organisation on GitHub, and the forum post gave the
  batch attention before it arrived. Its account counts as an outside contributor, but the batch
  is not a typical outside contribution.
- We labelled closures and disputes by hand from the comments, and could see which items were
  from the batch while doing it.
- The outside comparison covers twelve weeks, when maintainers' load may have differed. Only 7
  small outside PRs and 3 outside issues arrived in the same days as the batch, too few to compare.
- The all-PR row leaves out 85 "Bump stdlib" PRs from an account GitHub lists as a user, not a
  bot, so our bot filter kept them. We noticed this after counting. With them, the outside rate
  is 93 of 253 (36.8%). The small-PR comparison contains none of them.

## Reproduce

All inputs are public: GitHub's search, pull request, timeline and comment APIs for
JuliaLang/julia. [`reproduce/`](reproduce/) holds the fetch and analysis scripts, the rules we
wrote before counting, the summary output, and our hand labels with the quote that decides each.
Logins other than the author's are replaced by role labels; the scripts rebuild the full data
from GitHub. See [`reproduce/README.md`](reproduce/README.md).

We ran this once on our own machine, and recounted the headline numbers from the saved API
responses with a separately written script. Nobody outside the company has
reproduced it.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai. We will publish dated corrections here.
