"""Registry history: every commit to gittensor/validator/weights/master_repositories.json in entrius/gittensor, up to the
last list commit (884ce17, 2026-10-12, empty list).

python3 src/fetch_registry.py [CLONE_DIR]   (clones https://github.com/entrius/gittensor into CLONE_DIR if it is missing)

Writes raw/whitelist_commits.json (newest first: sha, author date in UTC, subject) and raw/wl/<sha>.json (the file's bytes
at each commit). registry.py uses the author date as the list date. For the 2026-04-09 removal (faa56734, #356) the
committer date is 19 h later, 2026-04-10T16:39:31Z; removal_windows.py reports that variant too.
"""
import json, os, subprocess, sys
from datetime import datetime, timezone
PATH = 'gittensor/validator/weights/master_repositories.json'
LAST = '884ce1785f802f384b1f13a9df87ba29d9cbe821'
clone = sys.argv[1] if len(sys.argv) > 1 else 'gittensor'
if not os.path.isdir(os.path.join(clone, '.git')):
    subprocess.run(['git', 'clone', '--quiet', 'https://github.com/entrius/gittensor', clone], check=True)
git = ['git', '-C', clone]
log = subprocess.run(git + ['log', '--format=%H%x00%aI%x00%s', LAST, '--', PATH], check=True, capture_output=True, text=True).stdout
cs = []
for line in log.splitlines():
    sha, date, msg = line.split('\0')
    cs.append({'sha': sha, 'date': datetime.fromisoformat(date).astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'msg': msg})
os.makedirs('raw/wl', exist_ok=True)
for c in cs:
    blob = subprocess.run(git + ['show', f"{c['sha']}:{PATH}"], check=True, capture_output=True).stdout
    open(f"raw/wl/{c['sha']}.json", 'wb').write(blob)
json.dump(cs, open('raw/whitelist_commits.json', 'w'), indent=1)
print(len(cs), 'commits', cs[-1]['date'], '..', cs[0]['date'])
