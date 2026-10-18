# "One of twelve children," then twelve siblings: what a consistency check finds in edited AI family biographies

A genealogy writer gives an AI model a sourced research sketch of an ancestor and asks for a readable biography, with an explicit instruction not to add or embellish details. The writer then edits the draft for accuracy and publishes it. How often does the published text still contradict itself?

We checked 30 of these biographies. In 13 of them, the AI had introduced at least one contradiction that was not in the writer's notes, and the edit had left it in place. Asking a model to check the draft against those notes found 23 of the 24 we counted.

## The material

[Genea-Musings](https://www.geneamusings.com/), a long-running genealogy blog, has published about 75 "ABC Biography" posts since April 2025. Each post shows its whole pipeline: the author's own research sketch (linked), the prompt ("do not add or embellish any extra genealogical details"), and the biography written by a Claude model (3.7, then Sonnet 4, 4.5 and 4.6), labelled as AI-written and often as "lightly edited". Because the source sketch is public next to the result, anyone can check the biography against its own input. That openness is what made this check possible; it is also more disclosure than most AI-assisted family history gets.

## What we did

- 65 posts were eligible. We left out posts without a biography section, the post we used to build the check, and one about a person born after 1900. We drew 30 with a fixed random seed.
- A checking pass (a Claude model, run fresh for each post) read the biography and the sketch in random order, without being told which one was AI-written, and listed passages that contradict each other within the same document.
- An AI reviewer, working from written rules, checked every flagged item against the text: is it a real contradiction, and did the biography introduce it, or copy it from the sketch? The reviewers knew which document was the biography.
- The checking rules and the decision threshold were fixed before any labels were read. Several judgment rules (for example, an age reported from a census does not count) and the line between minor and material were written down during the review and are published with the data.
- A second AI reviewer made its own calls on all 78 flagged biography items before seeing the first review's verdicts. The two agreed on 66 of 78 items (Cohen's kappa 0.69). Every disagreement that changed a post's result went the same way: the first review had counted four posts that the second did not, two by misapplying the rule for what counts as copied from the notes and two on vague wording ("final major move", "remaining years in this western Pennsylvania community"). The first review rechecked those items against the text and accepted the corrections, so the figures below are the stricter count. The first review's original count was 17 of 30. Neither review is a human genealogist's.

## What it found

| | posts of 30 |
|---|---|
| Biography has at least one contradiction the AI introduced | **13** (43%; 95% CI 27–61%) |
| ... of which material: wrong count, wrong relationship, impossible sequence, place, or age off by 2+ years\* | **12** (40%; 95% CI 25–58%) |

\* Descriptive. The line between minor and material was drawn during the review, not fixed in advance.

That is more than a third of the sample, and the most likely value is around four in ten. Thirty posts cannot pin it down more tightly than that.

Some examples, quoted from the published biographies:

- "two infant sons both named John Rich", followed by "The second son, William".
- A Nathaniel who is "his brother" in one paragraph and "their son" in another.
- "After thirty-one years of marriage" for a couple married in May 1813 when the wife died in February 1865.
- "Benjamin was one of twelve children", followed by a list of twelve siblings.

Of 44 real contradictions in the biographies, 20 were copied from the sketch and 24 were introduced by the AI. The introduced ones are arithmetic and summary errors, not typos: ages and dates that do not match each other (9, three of them in one sentence), counts and spans such as children, siblings or years of marriage (8), sequence and superlatives, such as a sister who "lived the longest of all the siblings" and did not (3), relationships and identity (3) and place (1).

## The fair comparison

The author's research notes are not cleaner. The same check found an internal conflict in 25 of 29 sketches, mostly a date that differs between the fact list and the narrative notes (one is a birth year typed as 1948 for a man who died in 1917). Nearly half of the real contradictions in the biographies (20 of 44) were copied straight from those notes. That is not evidence that the AI writes less consistently than the human.

The difference is in kind and in what happens next. A sketch is a set of working notes that repeats each date in several places, so a typo in one place shows up next to the right value. A biography is the polished family story: it is the version relatives read, and the blog also uses these biographies as input for AI life memoirs, and publishes AI songs, poems and audio and video overviews about its ancestors. An AI error in it is a reasoning error (a count, a sequence, who is whose relative) that reads smoothly and carries the narrator's confidence.

Newer models did not remove it in this sample: by the model named in each post, Claude 3.7 had 1 of 3, Sonnet 4 had 6 of 15, Sonnet 4.5 had 4 of 10, and Sonnet 4.6 had 2 of 2. These groups are too small to rank models.

## The check that catches most of them

The light edit is the step that misses these. What found them in our test was a request any family historian could type. We gave a model the biography with the research notes underneath and wrote:

> I'm a family historian. An AI wrote the biography below from my research notes (the notes follow it in the
> same file). Before I publish the biography, please check it for errors I should fix.

On the same 30 posts, that request found 23 of the 24 contradictions the AI introduced, and flagged at least one in 12 of the 13 affected biographies. The one it missed was a list introduced as "Their surviving children" that included a daughter who died as an infant. No special prompt or tool was needed. The step that matters is giving the model your notes, not only the draft, and asking before you publish.

It also over-reports. It returned about 12 items per biography, many about details that are not in the notes at all; we did not check how many of those are real. Treat its list as places to look in your sources, not as corrections to paste in.

## Limits

- One author's pipeline and one family's research, 30 posts. This is not a rate for AI biographies in general.
- We measured only contradictions inside the biography. Nothing was checked against records, so a biography with none of these can still be wrong.
- 13 counts only what one checking pass flagged and the reviews upheld. The pass misses some contradictions (its recall is unknown), so the true share could be higher. The reviewers are AI models and could be wrong in either direction. Counting the two vague statements above would give 15.
- The checking pass behind the main result over-reports too: 56% of what it flagged in the biographies held up (44 of 78). 20 of the 34 false alarms restated a census or passenger-list record, usually an age, which often disagrees with the birth date anyway; one post contributes 6 of them.
- The checking pass, both reviewers and the model in the plain-request test are Claude models, the same family that wrote the biographies. They may share blind spots, which is a reason to discount our checker.
- Two of the 30 posts link a sketch that is partly or wholly about another family. In the one with no matching sketch at all, we could not tell copied from introduced and counted its two contradictions as introduced; without that post the result is 12 of 29.
- The author's later memoir stage (a newer model) corrected all three errors in the one pilot biography, outside the sample of 30, that we followed that far, and added a note listing invented and assumed details. That is one example, not a rate.

## Data

[`posts.csv`](posts.csv) lists the 30 posts with links, the model each names, and the per-post results. [`items.csv`](items.csv) lists all 78 flagged biography items, the 34 not upheld as well as the 44 real ones, with two short excerpts each and the reviewer's verdict. [`DATA.md`](DATA.md) explains the columns and what is not included. `python3 recount.py` recomputes every number above from those two files; its output is in [`run-recount.txt`](run-recount.txt). `SHA256SUMS` lists the file hashes.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai. We publish corrections as dated notes on this page.
