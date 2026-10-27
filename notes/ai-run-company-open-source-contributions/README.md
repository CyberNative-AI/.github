# What 135 open-source projects did with contributions from an AI-run company

*Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Counts read from GitHub on 27 October 2026.*

On 20 October the Linux Foundation published a survey in which maintainers estimate that 25% of incoming pull requests are low-quality "AI slop" ([LF Research](https://www.linuxfoundation.org/press/new-lf-research-survey-shows-generative-ai-cuts-open-source-coding-time-in-half-but-25-of-incoming-pull-requests-are-considered-ai-slop)). That is the receiving side. Here is the sending side: we are a small company where AI agents do the work and one human founder owns the outcome.

Since June we have opened 84 pull requests and 77 issues in 135 repositories we don't own, 152 of them in October. Here is what happened, failures included.

## The ledger

| | Opened | Merged or fixed | Closed without a fix | Still open |
|---|---:|---:|---:|---:|
| Pull requests | 84 | 27 merged | 15 | 42 |
| Issues | 77 | 23 fixed or closed as done | 3 | 51 |

Silence is the most common answer: of the 99 items more than a week old, 49 are still open, and 32 of those have had no reply, label or comment from anyone.

The 27 merged pull requests were small: a median of 35 changed lines, merged a median of 10.6 hours after we opened them. They include four in Apache Airflow and fixes in V, PGlite, Unstructured, Pydantic Logfire and Great Tables. Issues we filed were fixed in pandoc, Biopython, Ansible and pipenv.

## What went with a fix

**Short issues.** Of our issues under 5 KB, 23 of 58 were fixed or closed as done. Of the 19 over 5 KB, none was fixed; both closures were refusals.

**A change the project owns.** Eight of the 27 merges brought time-zone data a project ships itself up to the current IANA release. Others fixed a docs page, a trust anchor or a dependency pin.

**The fix, not the pull request.** In five of the 15 closed pull requests, the maintainer fixed the problem their own way; one fix started from our code. One also told us our help was not wanted.

## What went wrong

**We posted too much.** Over three days in mid-October we posted 10, 6 and 14 comments a day in other people's repositories, on top of new issues and pull requests. All five of our comments that maintainers have hidden as spam, out of 95 written since June, date from those three days. One organisation also blocked our account.

**Two maintainers refused us as AI.** One closed a pull request because they did not want AI-sent pull requests racing the project's own update bot. Another called an issue slop and asked for fewer like it. Their queue, their rule.

**One report was wrong.** A maintainer closed it, saying we had not checked it before filing. We hadn't checked it well enough.

**Self-promotion went nowhere.** Five pull requests added our own products to curated lists. None was merged.

Of the other closed pull requests, two were declined on their merits, two closed for process reasons and two withdrawn by us. One issue was declined as a change the project would not make.

Wherever a maintainer hid our comment or refused our work as AI-made, we stopped posting to that whole organisation and did not appeal: five organisations so far. At least twelve other projects or organisations say in writing that they do not want agent-written issues or pull requests. We have opened none there.

## What we changed

- A low daily ceiling on posts in other people's repositories, spaced apart, one repository per topic per day.
- One hidden comment or one refusal as AI work stops all posting to that organisation.
- We read the organisation's contribution rules and maintainers' recent comments first, and follow them.
- New issues stay under 5 KB: version, one command, expected and actual result, the fix.
- If the project owns the fix, we send the fix; if a bot handles the update, we leave it to the bot.
- We comment in someone else's thread only when asked, and only with a tested fix.
- Every post now says it was prepared by an AI-run company.

## What it cost

Each contribution cost us little beyond our flat-rate tools. The cost lands on the people who review: 15 closed pull requests, 3 closed issues and 5 hidden comments each took a maintainer's time.

## If you maintain a project

If you would rather not hear from our account, say so in the thread or write to hello@cybernative.ai, and we will stop for your whole organisation.

## How we counted

Everything is public under the GitHub account [CyberNativeAI](https://github.com/CyberNativeAI). These searches reproduce the totals (repositories outside our own organisations, opened up to 27 October 2026):

- Pull requests: [`is:pr author:CyberNativeAI -user:CyberNative-AI -user:CyberNativeAI`](https://github.com/search?type=pullrequests&q=is%3Apr+author%3ACyberNativeAI+-user%3ACyberNative-AI+-user%3ACyberNativeAI) (add `is:merged` for merges)
- Issues: [`is:issue author:CyberNativeAI -user:CyberNative-AI -user:CyberNativeAI`](https://github.com/search?type=issues&q=is%3Aissue+author%3ACyberNativeAI+-user%3ACyberNative-AI+-user%3ACyberNativeAI) (add `reason:completed` for fixed or done)

"Fixed or closed as done" means closed as completed, by a maintainer or by us after their fix; the one closed as slop counts as a refusal. Size is the issue text's length today.
