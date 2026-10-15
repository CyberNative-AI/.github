#!/usr/bin/env python3
"""Rebuild GitHub's retired push-notification email from an Actions `push` event.

GitHub stopped sending repository push emails on 2026-10-15. This script writes
the same plain-text message (subject, Branch/Home/Commit/Author/Date, Changed
paths, Log Message, Compare) and sends it through your own SMTP server.

Commit list, order, authors and messages come from the event payload. The
payload Actions receives has no added/removed/modified lists, so the committer
date and changed paths come from git: check out with fetch-depth: 0.

Standard library only. Configuration is by environment variable:
  SMTP_HOST, SMTP_PORT (587), SMTP_SECURITY (starttls, the default | ssl | none;
  any other value stops the script),
  SMTP_USER, SMTP_PASSWORD, MAIL_FROM, MAIL_TO (comma-separated),
  MAIL_APPROVED (optional Mailman `Approved:` password), DRY_RUN=1 to print only.
"""
import json
import os
import smtplib
import ssl
import subprocess
import sys
from datetime import datetime
from email.message import EmailMessage
from email.policy import SMTP
from email.utils import formatdate, make_msgid


def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else None


def have_commit(sha):
    return git("cat-file", "-e", sha + "^{commit}") is not None


def git_details(sha):
    """Committer date (own zone) and name-status lines, as the old email showed them."""
    # Not `git show -s`: it still runs rename detection, which in a blob-less
    # clone fetches file contents, and fails in a private repo without credentials.
    fields = git("log", "-1", "--format=%cI%x00%P", sha)
    if fields is None:
        raise SystemExit(f"git could not read commit {sha}; nothing sent")
    date, _, parents = fields.strip().partition("\0")
    parents = parents.split()
    # -z: raw paths, not git's quoted "caf\303\251" form for unusual names.
    base = [parents[0], sha] if parents else ["--root", "--no-commit-id", sha]
    diff = git("diff-tree", "-r", "-z", "--no-renames", "--name-status", *base)
    if diff is None:
        raise SystemExit(f"git could not read commit {sha}; nothing sent")
    parts = diff.split("\0")
    paths = []
    for status, path in zip(parts[0::2], parts[1::2]):
        # The old email printed the payload's lists: A added, R removed, M modified.
        paths.append(({"D": "R"}.get(status[0], status[0]), path))
    return datetime.fromisoformat(date), paths


def render(event, repo, server="https://github.com"):
    """Return (subject, body) for a push that carries commits."""
    home = f"{server}/{repo}"
    commits = event["commits"]
    missing = [c["id"] for c in commits if not have_commit(c["id"])]
    if missing:
        raise SystemExit(f"{len(missing)} pushed commits are not in the local clone "
                         f"(first {missing[0]}); check out with fetch-depth: 0")
    body = f"  Branch: {event['ref']}\n  Home:   {home}\n"
    for c in commits:
        date, paths = git_details(c["id"])
        author = c["author"]
        body += (f"  Commit: {c['id']}\n      {home}/commit/{c['id']}\n"
                 f"  Author: {author['name']} <{author['email']}>\n"
                 f"  Date:   {date:%Y-%m-%d} ({date:%a, %d %b %Y})\n\n"
                 "  Changed paths:\n")
        body += "".join(f"    {s} {p}\n" for s, p in sorted(paths, key=lambda x: x[1]))
        body += f"\n  Log Message:\n  -----------\n  {c['message'].rstrip()}\n\n\n"
    if len(commits) > 1:
        # The payload's own link; for a new branch `before` is all zeros.
        compare = event.get("compare") or f"{home}/compare/{event['before'][:12]}...{event['after'][:12]}"
        body += f"Compare: {compare}\n"
    first = commits[0]
    title = first["message"].splitlines()[0]
    if len(title) > 53:
        title = title[:50] + "..."
    return f"[{repo}] {first['id'][:6]}: {title}", body


def main():
    # Check before anything else: a misspelled value must not fall back to plain SMTP.
    security = os.environ.get("SMTP_SECURITY") or "starttls"
    if security not in ("starttls", "ssl", "none"):
        raise SystemExit(f"SMTP_SECURITY must be starttls, ssl or none, not {security!r}; nothing sent")
    event = json.load(open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8"))
    repo = os.environ["GITHUB_REPOSITORY"]
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    if event.get("deleted") or not event.get("commits"):
        print("push has no new commits (branch/tag deletion or ref move); nothing sent")
        return 0
    subject, body = render(event, repo, server)
    body += f"\n-- \nSent by the {os.environ.get('GITHUB_WORKFLOW', 'push email')} workflow in {repo}.\n"

    msg = EmailMessage(policy=SMTP.clone(max_line_length=998))  # keep Subject on one line
    pusher = (event.get("pusher") or {}).get("name") or "GitHub"
    sender = os.environ["MAIL_FROM"]
    msg["From"] = f"{pusher} <{sender}>" if "<" not in sender else sender
    msg["To"] = os.environ["MAIL_TO"]
    msg["Subject"] = subject
    msg["Date"] = formatdate(usegmt=True)
    msg["Message-ID"] = make_msgid(domain=sender.rsplit("@", 1)[-1].strip(">"))
    msg["X-Auto-Response-Suppress"] = "All"
    msg.set_content(body, cte="quoted-printable")

    if os.environ.get("DRY_RUN") == "1":
        # The preview leaves out Approved:, which carries the list password.
        if os.environ.get("MAIL_APPROVED"):
            print("(MAIL_APPROVED is set; the sent email also has an Approved: header)", file=sys.stderr)
        sys.stdout.write(msg.as_string())
        return 0
    if os.environ.get("MAIL_APPROVED"):
        msg["Approved"] = os.environ["MAIL_APPROVED"]
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT") or (465 if security == "ssl" else 587))
    ctx = ssl.create_default_context()
    smtp = (smtplib.SMTP_SSL(host, port, context=ctx, timeout=60) if security == "ssl"
            else smtplib.SMTP(host, port, timeout=60))
    with smtp:
        if security == "starttls":
            smtp.starttls(context=ctx)
        if os.environ.get("SMTP_USER"):
            smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        smtp.send_message(msg, to_addrs=[a.strip() for a in os.environ["MAIL_TO"].split(",")])
    print(f"sent: {subject}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
