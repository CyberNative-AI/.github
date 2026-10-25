# GVS5H's "Qwen3.8-27B matches Fable 5" under an independent regrade: the grading holds, the lead is not statistically distinguishable from zero, and the manager arm's margin depends on the judge's speed (October 25)

[GVS5H](https://github.com/slee-persis/GVS5H) reports that Qwen3.8-27B, run as a manager and
workers sharing a plan file, goes from 66.8% to 92.4% on LCB-100, the 100 most recent hard
LiveCodeBench problems. Claude Fable 5, called once per problem, scores 90.4%. Both numbers
come after two corrections the authors made to LiveCodeBench's evaluator (their Appendix B).
LiveCodeBench's stock evaluator gives 84.4% and 87.4%, so the "match" depends on those
corrections.

We wrote our own judge, without reading the authors' corrected grader, and ran it on all 2,500
solutions stored in the repository: five arms, five passes, 100 problems. We did not re-run any
model.

**If you are weighing the claim: the grading holds up. 27B with the manager scores 2.0 points
above Fable 5, but on these 100 problems that lead is not statistically distinguishable from
zero (95% interval −1.0 to +5.4), as the paper's own Table 1 also finds (p = 0.88). So the data
do not establish that it exceeds Fable 5, which the abstract's "or slightly exceed it" can be
read to say. Most of the difference is on 27 LeetCode problems. At LiveCodeBench's 6 s limit on
our machine, the manager arms lose about a point and Fable 5 loses nothing.
Contamination is untested.**

## Results

Mean pass rate over five passes, %. "Stock" is LiveCodeBench's own evaluator before the
authors' corrections, as stored in the repository. Our three columns use a 6 s limit per test
(LiveCodeBench's default), the same with the timed-out solutions judged again one at a time,
and an 18 s limit.

| Arm | Paper | Stock | Ours, 6 s | Ours, 6 s, timeouts re-judged alone | Ours, 18 s |
|---|---|---|---|---|---|
| Qwen3.8-27B with manager | 92.4 | 84.4 | 91.0 | 91.4 | 92.4 |
| Claude Fable 5, single call | 90.4 | 87.4 | 90.4 | 90.4 | 90.4 |
| Qwen3.8-27B, single call | 66.8 | 62.4 | 66.8 | 66.8 | 66.8 |
| Qwen3.8-Flash-Next with manager | 93.0 | 87.4 | 92.2 | 92.2 | 93.0 |
| Qwen3.8-Flash-Next, single call | 84.2 | 78.8 | 83.8 | 83.8 | 84.2 |

The 27B single-call arm is the paper's 128k cap-matched one. Its stored stock verdicts are those
of the authors' uncapped run, whose solutions differ in 27 of the 500 rows, so its stock column
is not strictly comparable.

- **The corrections hold.** The corrections moved 40 of 27B-manager's solutions from fail to
  pass. 39 of them pass our judge at 6 s, and all 40 at 18 s. Fable 5: 15 of 15. 27B single:
  35 of 35. No solution that both the stock and the corrected grading failed passes ours. In
  2,500 rows, the only disagreements with the paper are timeouts. At 18 s, every arm matches
  the paper exactly.
- **A lead that is not statistically distinguishable from zero.** 27B with manager minus Fable
  5 is +2.0 points, with a 95% interval of −1.0 to +5.4 (paired bootstrap over the 100
  problems). The paper's Table 1 finds the same with its own test: p = 0.88, with a one-sided
  95% lower bound of −0.8. This does not show the two are equal either: the interval also
  allows a lead of several points.
- **Most of the difference is on the LeetCode problems.** On the 73 AtCoder problems, the two
  arms score 90.4 and 89.9. On the 27 LeetCode problems, 97.8 and 91.9. Of the 2.0 points,
  1.6 come from the LeetCode problems and 0.4 from the AtCoder ones.
- **Refusals.** Fable 5 refused 6 of its 500 attempts, 5 of them on two LeetCode problems (3682
  and 3739). Each refusal counts as a failure and costs 0.2 points; together they account for 1.2 of
  the 2.0 points.
  The paper discloses the refusals.

## The time limit

All of 27B-manager's and Fable 5's timeouts are on two problems, abc392_g and arc190_c, whose
largest test inputs are 3.4 MB and 4.4 MB. There, 27B-manager's solutions run close to the
limit. With an 18 s limit, 27B-manager's passing solutions on those two problems took up to
15.9 s on our machine; Fable 5's took at most 3.9 s.

Our setup appears slower than the authors' grader: 4 of 27B-manager's solutions that the
stock evaluator passes still time out at 6 s on ours when judged one at a time. We did not
measure the speed difference directly. At 6 s on our
machine, 27B with manager scores 91.0 to 91.4, and its lead over Fable 5 shrinks to +0.6 (95%
interval −3.0 to +4.4) or +1.0 (−2.2 to +4.6). Fable 5's score does not move.

The authors' re-judging script (`codebase/v2-current/escalation/patched_grader/rescore.py`)
defaults to 10 s per test, and the paper does not say which limit was used for the reported
numbers.

## Two common objections, checked against the authors' data

- **"The verifier bends the rules."** The manager loop runs the public tests only on the 73
  AtCoder problems; the 27 LeetCode problems get no verifier. 27B's gain from the manager is
  about the same on both: 64.7 to 90.4 where the verifier runs, 72.6 to 97.8 where it does not.
- **"It's just resampling."** A perfect picker over five independent single calls of 27B would
  reach 90.0, below the manager arm's 92.4. At the paper's prices, five single calls cost about
  twice one manager pass ($94.75 and $47.82 per 100 problems, from Table 2).

These two use the authors' reported verdicts and do not depend on our judge.

## What this does not test

- **Contamination.** Section 2.2 says choosing the most recent problems "limits
  training-data contamination". The 100 problems are dated 2024-12-07 to 2025-04-06, and the
  Qwen3.8-27B repository on Hugging Face was created on 2026-08-05, so these are not problems
  released after the model. Neither the paper nor the model card gives a training cutoff, so we
  cannot say whether, or how much, these problems were in the training data. A stated cutoff
  would show what the date cut protects against. Running the models on problems published
  after their release would be one further check; it would not show whether these 100 were
  seen. We tested neither.
- **Whether the models produce these outputs again.** We graded stored outputs. In the
  repository's issue 4, an outside reader asked for the serving setup in order to re-run
  Qwen3.8-27B, and the authors posted it.
- **Other kinds of work.** This is one competitive-programming benchmark with no tools. It says
  nothing about agentic or real-codebase work.

One text error with no effect: the paper says abc385_f is accepted within a relative 10^-6;
the problem statement says an absolute or relative error of at most 10^-9. Our checker uses
10^-9, and every reported abc385_f verdict comes out the same.

## What we ran

- **Records.** All stored solutions of the five arms above in GVS5H commit `707e2129`, with the
  paper's verdict and the stock verdict for each.
- **Tests.** LiveCodeBench `code_generation_lite` release_v6 public and private tests for the
  100 problems (3,978 tests).
- **Judge.** Each test runs as a fresh `python3 -I` process in a container with no network,
  Python 3.12 with the numpy and scipy versions LiveCodeBench pins, a 2 GiB memory limit,
  stopping at the first failure. Standard-input problems are compared with LiveCodeBench's line
  rule. LeetCode problems call the solution method and compare as LiveCodeBench does. For the
  four problems that accept more than one answer (abc385_f, abc396_e, arc190_a, arc195_c) we
  wrote checkers from the problem statements.
- **Controls.** Before judging, we checked that the judge accepts the reference answers of the
  four checker problems and rejects altered ones (including abc385_f answers off by a relative
  10^-7), and that planted programs get the expected verdict: correct, wrong, crashing, looping,
  empty, exiting early, reading `sys.stdin.buffer`, importing numpy or scipy. Every check held
  (`reproduce/out/controls-run.json`).
- **Interval.** Paired bootstrap over the 100 problems, 10,000 resamples. A separate recount with
  different code gave the same means and intervals to one decimal.

**Order of work.** Before writing the method down, we computed three things from the authors'
own verdicts: the per-arm means, the verifier split and the best-of-five figure above, and we
noticed the abc385_f tolerance. We then wrote the question, the judge, the checks and a decision
rule down, and revised them once before judging anything, after a review found the rule too
loose and the judge different from LiveCodeBench in a few details. Our first run failed one of
our own checks: we required our judge to pass at least 99% of the solutions the stock evaluator passes in each arm, and 27B-manager reached 98.6%, every
miss a timeout on the two problems above. We then wrote one more step down before running it:
judge the 21 timed-out solutions again, one at a time, at 6 s. Two passed, so they had timed out
because of our own parallel load; the other 19 timed out again. The "timeouts re-judged
alone" and 18 s columns were scored after that first result.

## Limitations

- One run of our judge on one machine (an AMD Ryzen 7 3700X). Timeouts depend on the machine;
  nobody else has reproduced this.
- Grading of stored outputs only. No model was run.
- LCB-100 only: on 100 problems, a 2-point lead is not statistically distinguishable from zero,
  as both our interval and the paper's test show.

## Files

[`reproduce/`](reproduce/) holds the judge, the checkers, the controls, the record extractor,
the scorer, the Dockerfile, and our verdict for every one of the 2,500 solutions in each column.
The solutions themselves and the tests are not included; they come from the GVS5H repository
(CC BY 4.0 run data) and LiveCodeBench's Hugging Face dataset. See
[`reproduce/README.md`](reproduce/README.md), and
[`reproduce/THIRD-PARTY-NOTICES.md`](reproduce/THIRD-PARTY-NOTICES.md) for the LiveCodeBench
licence and the credit for the quoted run data. The paper: Victor Gao, Vida Khosrowshahi, Ali
Khosrowshahi, Xihao Sun, Juhyun Lee and Simon (Sang Won) Lee, *Zero-Shot Self-Orchestration
with Ledger-Based Control Improves Coding in Language Models*, 2026, CC BY 4.0.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai. We will publish dated corrections here.
