# GitHub stopped sending push emails. Here is the same email from Actions.

On 15 October 2026 GitHub [retired email notifications for repository push events](https://github.blog/changelog/2026-10-15-email-notifications-for-repository-push-events-have-been-retired). If a mailing list such as `project-commits@` was subscribed through **Settings → Email notifications**, it receives nothing from the next push on. GitHub's advice is to send the email yourself from a GitHub Actions workflow. This folder contains that workflow, and it sends the same email the feature used to send.

Lists were still receiving these emails on the day of the retirement: [qemu-commits](https://lists.gnu.org/archive/html/qemu-commits/2026-10/) got one at 13:04 UTC on 15 October.

## Use it

1. Copy [`push_email.py`](push_email.py) to `.github/scripts/push_email.py` and [`push-email.yml`](push-email.yml) to `.github/workflows/push-email.yml`. Put both on **every branch that should send mail**. A push runs the workflows in the pushed commit ("This includes workflows that are not merged into the default branch", [GitHub docs](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#push)).
2. Add repository secrets `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `MAIL_FROM` and `MAIL_TO`. `SMTP_PORT` is optional and defaults to 587 with STARTTLS. For a server that uses TLS from the first byte on port 465, change `SMTP_SECURITY` in the workflow to `ssl`. The script stops on any value it does not know, instead of falling back to an unencrypted connection. For a Mailman list that holds non-member posts, add `MAIL_APPROVED`; it is sent as an `Approved:` header.
3. Push a commit, then check the list archive. To see the message before it reaches the list, add `DRY_RUN: "1"` to the step's `env:` first; the job log then shows the email and nothing is sent. The preview leaves out the `Approved:` header, because it carries the list password.

The script uses only the Python standard library.

## What "the same email" means, and how we checked it

The script writes GitHub's subject (`[owner/repo] abc123: first line`, with a long first line cut to 50 characters plus `...`) and GitHub's body: Branch, Home, then for each commit Commit, Author, Date, Changed paths and Log Message, and a Compare link when the push has more than one commit.

We tested it against the raw qemu-commits archive for October 2026 ([mbox](https://lists.gnu.org/archive/mbox/qemu-commits/2026-10)). That archive holds 40 emails GitHub sent. One push moved a branch without adding commits, so it has no commit blocks. For each of the other 39, we took the commit IDs in the email's order, rebuilt the message from a clone of qemu and compared the result with the archived email. **All 39 subjects and bodies are byte-identical**, from the start of the body to GitHub's unsubscribe footer. That covers 1,109 commit blocks, including merges and pushes of up to 106 commits.

```sh
git clone --bare --filter=blob:none --shallow-since=2026-08-01 https://github.com/qemu/qemu.git qemu.git
curl -so qemu-commits-2026-10.mbox https://lists.gnu.org/archive/mbox/qemu-commits/2026-10
python3 corpus_check.py qemu-commits-2026-10.mbox qemu.git qemu/qemu
# 39 byte-identical, 0 different, 1 skipped; 1109 commit blocks checked
```

Matching the old email needed three details that are easy to get wrong:

- **`R` means removed, not renamed.** GitHub printed `A` (added), `R` (removed) and `M` (modified), and a renamed file appeared as an `A` line plus an `R` line. If you use `git diff --name-status` with rename detection, the output differs whenever a file moves.
- **The Date line is the committer date in the committer's own time zone.** It matched in all 1,109 blocks. The author date matched in 88.
- **Merge commits list paths against their first parent.**

## The Actions payload has no file list, so the workflow fetches history

The push payload that Actions receives "does not include the `added`, `removed`, and `modified` attributes" ([GitHub docs](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#push)). If a workflow builds the email from `github.event` alone, it can't print the Changed paths section. This workflow checks out with `fetch-depth: 0` and `filter: blob:none`, which fetches commits and trees but no file contents, and reads the paths and committer dates from git. If a pushed commit is missing locally, the script stops with an error. It does not send an email with the paths missing.

A blob-less clone has one more trap. Read commit fields with `git log -1 --format=...`, not `git show -s`. `git show -s` prints no diff, but it still runs rename detection, and in a blob-less clone that downloads the contents of added and deleted files. In a public repository this only costs time. In a private repository checked out with `persist-credentials: false`, the download fails. Our first multi-commit run on Actions failed exactly this way, on a commit that renamed one file and deleted another.

## Pushes that send no email, or a shorter one

The first four are Actions rules, not script choices:

- **More than three tags pushed at once.** "Events will not be created for tags when more than three tags are pushed at once." This workflow skips tag pushes anyway, because a tag push brings no new commits.
- **More than 5,000 branches pushed at once.** No event is created.
- **Pushes made with a workflow's `GITHUB_TOKEN`**, such as a bot that commits from another workflow. "Events triggered by the `GITHUB_TOKEN` will not create a new workflow run" ([GitHub docs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)); `push` is not one of the exceptions.
- **Pushes of more than 2,048 commits.** The payload lists at most 2,048 commits ([webhook docs](https://docs.github.com/en/webhooks/webhook-events-and-payloads#push)), so the email lists at most 2,048.
- **Branch deletions and pushes with no new commits.** The old feature sent an email with only the Branch and Home lines. This workflow sends nothing.

Two things differ from the old email by design. The sender is your `MAIL_FROM` address, shown with the pusher's GitHub login as the display name. The footer names the workflow, because the old link to the repository's notification settings no longer applies.

## Limits

- **Tested:** the byte comparison above; a local end-to-end run ([`e2e_test.sh`](e2e_test.sh)); and four pushes to a private test repository on GitHub Actions on 15 October 2026, with the workflow's SMTP server replaced by a sink inside the job. The second push found the `git show -s` problem above; the script stopped and sent nothing. After the fix, we rendered the emails from the last two runs again from a full clone, using the payload each run received. In both, the Subject and the decoded body matched byte for byte; the Date and Message-ID headers differ, because the script generates them for each send. Those two pushes covered a rename, deletions, file names with a space and with a non-ASCII letter, a merge, a long subject and a new branch.
- **Commit order:** the script uses the order in the payload. In our three live pushes with more than one commit, that order was `git rev-list --reverse before..after`. In the qemu archive, 37 of the 38 multi-commit emails use that order ([`order_check.py`](order_check.py)). The other is a push of 49 commits, most of which share a committer timestamp with another, and it follows `git rev-list --reverse --topo-order` instead. None of our live pushes had shared timestamps, so we have not confirmed what the payload does in that case.
- **Unusual file names** are printed as they are, in UTF-8. The qemu archive has none, so we could not compare this with an old email.
- Actions minutes: each push runs one short job. For a private repository, these minutes count against your plan.
- The checkout fetches the full history without file contents, on every push. On a large repository, that takes noticeable time.

Files: `push_email.py` (script), `push-email.yml` (workflow), `corpus_check.py` (byte comparison), `order_check.py` (commit order against the archive), `e2e_test.sh` + `smtp_sink.py` (local end-to-end test).

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai. We publish
corrections as dated notes on this page.
