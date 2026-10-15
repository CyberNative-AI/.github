#!/bin/sh
# End-to-end: push_email.py sends to a local SMTP sink; the captured message is
# parsed and checked. Nothing leaves the machine. usage: sh e2e_test.sh
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
W=$(mktemp -d); SINK=
# Keep the test's own exit status; the sink has usually exited already.
cleanup() { st=$?; [ -z "$SINK" ] || kill "$SINK" 2>/dev/null || :; rm -rf "$W"; exit "$st"; }
trap cleanup EXIT
cd "$W"
git init -q -b main repo && cd repo
export GIT_AUTHOR_NAME="Ada Example" GIT_AUTHOR_EMAIL=ada@example.org GIT_COMMITTER_NAME="Ben Example" GIT_COMMITTER_EMAIL=ben@example.org
GIT_AUTHOR_DATE="2026-10-01T09:00:00+02:00" GIT_COMMITTER_DATE="2026-10-01T09:00:00+02:00" sh -c 'echo a > a.txt && echo b > b.txt && git add . && git commit -qm "Initial import"'
BEFORE=$(git rev-parse HEAD)
git checkout -qb topic
GIT_AUTHOR_DATE="2026-10-02T23:30:00-07:00" GIT_COMMITTER_DATE="2026-10-14T23:30:00-07:00" sh -c 'git mv a.txt renamed.txt && git rm -q b.txt && echo c > c.txt && git add c.txt && git commit -qm "Rename a, drop b, add c

Body line one.
Body line two."'
git checkout -q main
GIT_COMMITTER_DATE="2026-10-15T01:00:00+00:00" sh -c 'echo m >> c2.txt && git add c2.txt && git commit -qm "Add a file on main whose subject line is long enough that GitHub truncated it"'
GIT_COMMITTER_DATE="2026-10-15T02:00:00+00:00" git merge -q --no-ff topic -m "Merge branch topic"
AFTER=$(git rev-parse HEAD)
python3 -I - "$BEFORE" "$AFTER" > "$W/event.json" <<'PY'
import json, subprocess, sys
before, after = sys.argv[1:3]
ids = subprocess.run(["git", "rev-list", "--reverse", f"{before}..{after}"], capture_output=True, text=True).stdout.split()
def f(fmt, s): return subprocess.run(["git", "show", "-s", f"--format={fmt}", s], capture_output=True, text=True).stdout
commits = [{"id": s, "message": f("%B", s).rstrip("\n"), "timestamp": f("%aI", s).strip(),
            "author": {"name": f("%an", s).strip(), "email": f("%ae", s).strip()},
            "committer": {"name": f("%cn", s).strip(), "email": f("%ce", s).strip()}} for s in ids]
# Shape of the Actions push payload: no added/removed/modified lists.
print(json.dumps({"ref": "refs/heads/main", "before": before, "after": after, "deleted": False,
                  "pusher": {"name": "ben-example"}, "commits": commits}))
PY
export GITHUB_EVENT_PATH="$W/event.json" GITHUB_REPOSITORY=example/repo GITHUB_WORKFLOW="Push email" \
       SMTP_HOST=127.0.0.1 SMTP_PORT=2526 MAIL_FROM=commits@example.org MAIL_TO=list@example.org
# The preview must not show the list password, plain or MIME-encoded.
for pass in listpass "pässwörd-ü"; do
  DRY_RUN=1 MAIL_APPROVED="$pass" python3 -I "$HERE/push_email.py" > "$W/preview.eml" 2>/dev/null
  if grep -qi -e '^approved:' -e "$pass" -e '=?utf-8?' "$W/preview.eml"; then exit 1; fi
  grep -q '^Subject: \[example/repo\]' "$W/preview.eml"
done
# An unknown SMTP_SECURITY stops before any connection (nothing listens yet).
if SMTP_SECURITY=tls python3 -I "$HERE/push_email.py" 2> "$W/err.txt"; then exit 1; fi
grep -q "SMTP_SECURITY must be" "$W/err.txt"
python3 -I "$HERE/smtp_sink.py" 2526 "$W/captured.eml" & SINK=$!
sleep 1
SMTP_SECURITY=none MAIL_APPROVED=listpass python3 -I "$HERE/push_email.py"
wait $SINK; SINK=
python3 -I - "$W/captured.eml" <<'PY'
import email, sys
m = email.message_from_bytes(open(sys.argv[1], "rb").read())
body = m.get_payload(decode=True).decode().replace("\r\n", "\n")  # SMTP wire line endings
print("From:", m["From"]); print("To:", m["To"]); print("Subject:", m["Subject"]); print("Approved:", m["Approved"])
print(body)
subj = str(m["Subject"]).replace("\n", "")
assert subj == "[example/repo] " + subj.split("] ")[1] and subj.endswith("long enou...")
assert "    R a.txt\n    R b.txt\n    A c.txt\n    A renamed.txt\n" in body
assert "  Date:   2026-10-14 (Wed, 14 Oct 2026)" in body  # committer date, own zone
assert m["Approved"] == "listpass"  # a real send still carries it
assert body.count("  Commit: ") == 3 and "Compare: https://github.com/example/repo/compare/" in body
print("E2E PASS")
PY
