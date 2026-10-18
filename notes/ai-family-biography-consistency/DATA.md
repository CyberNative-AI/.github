# Data for "what a consistency check finds in edited AI family biographies"

Two files support the note in [README.md](README.md). `python3 recount.py` recomputes every number in the note from them (standard library only, no network); the output is in [run-recount.txt](run-recount.txt).

## posts.csv: the 30 sampled posts

| column | meaning |
|---|---|
| `post` | 1 to 30, in order of publication; joins to `items.csv` |
| `url` | the published "ABC Biography" post |
| `published` | publication date |
| `biography_model` | the model the post names as the biography's writer |
| `notes_url` | the author's research sketch the post links (space-separated if more than one) |
| `notes_match_post` | `yes`, `partly` (the sketch is partly about another family) or `no` (no part of it matches) |
| `biography_has_introduced` | the biography has at least one real contradiction that is not in the notes |
| `biography_has_introduced_material` | at least one of those is material (descriptive; see below) |
| `notes_have_own_conflict` | the sketch has at least one real internal conflict of its own; `not judged` for the post whose sketch matches no part of it |

## items.csv: all 78 flagged biography items

Every pair of passages the checking pass flagged in a biography is listed, including the 34 the reviewers did not uphold.

| column | meaning |
|---|---|
| `post` | joins to `posts.csv` |
| `quote_1`, `quote_2` | the two passages, as short verbatim excerpts (at most 22 words) with whitespace collapsed; one excerpt is trimmed to the words that show the contradiction |
| `real_contradiction` | `yes` if the reviewers upheld it as a contradiction within the biography |
| `source` | for real ones: `copied from notes` if the same conflict is in the author's sketch, `introduced` if not, `introduced (no matching notes)` for the post whose sketch matches no part of it |
| `material` | for introduced ones: `yes` for a wrong count, wrong relationship, impossible sequence, place, or an age off by 2 or more years |
| `kind` | for introduced ones: age or date, count or span, sequence, relationship, place |
| `plain_request_found` | for introduced ones: whether the plain "check it against my notes" request in the note flagged it |
| `reviewer_note` | the reviewer's reason, shortened. "Own-voice" means the biography states the age or date itself, as opposed to reporting what a census or passenger list said |

## How the verdicts were made

The checking rules and the decision threshold were fixed before any labels were read. Several judgment rules were written down during the review, after labels were read: an age reported from a census or passenger list does not count against a birth date; Old Style dates are read as such; a joint statement about a couple is not a claim about each person; a conflict counts as copied only if the sketch itself contains it. The line between minor and material was also drawn during the review, so the material column is descriptive.

The reviewers are AI models of the same family as the checking pass and the biography writers. A second review made its own calls on all 78 items before seeing the first review's verdicts; the first review then accepted its corrections. These files carry the corrected verdicts.

## What is not included

The checking pass also flagged 173 pairs inside the authors' sketches. They are not published here. For the 25 of 29 figure, the review stopped at the first upheld conflict in each sketch, so most of those pairs were never judged and should not be read as errors. `notes_have_own_conflict` in `posts.csv` carries that result per post, with the link to each sketch. The plain request's own over-reported items (about 12 per biography) were not adjudicated and are not listed.

## Source text

The excerpts are quoted from posts on Genea-Musings, which remain the copyright of their author, for criticism and research on the consistency of AI-written text. They are not covered by any license we give for this folder. Each row links back to its post through `post` and `url`.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai.
