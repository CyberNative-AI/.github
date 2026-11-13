# Count upcoming Breakage Calendar dates with a repository search, and how many Last Call also lists (read 2026-11-13).
# usage: python3 count_dates.py <entries.json> <signatures.json> <lastcall sunsets.json> [YYYY-MM-DD]
import json, sys, datetime
e = json.load(open(sys.argv[1]))['entries']; s = json.load(open(sys.argv[2]))
lc = json.load(open(sys.argv[3])); lc = next(v for v in lc.values() if isinstance(v, list))
today = datetime.date.fromisoformat(sys.argv[4] if len(sys.argv) > 4 else '2026-11-13')
sig = {x['row'] for x in s['signatures']}
MODEL = ('gemini-tts', 'sonnet-4-5', 'gpt-image', 'gpt-5', 'tts-1', 'gpt-4o', 'realtime', 'whisper', 'text-to-speech')
rows = [x for x in e if x['id'] in sig and datetime.date.fromisoformat(x['date']) >= today]
models = [x for x in rows if any(m in x['id'] for m in MODEL)]
other = [x for x in rows if x not in models]
print(f'upcoming with a repository search: {len(rows)}; AI-model rows: {len(models)}; others: {len(other)}')
# Hand-checked equivalents in Last Call (title search, 2026-11-13): only OpenAI Evals shuts down on the same date.
LC_SAME = {'2026-11-30-openai-prompts-evals-agent-builder-shut-down': 'OpenAI shuts down the Evals dashboard and API'}
for x in sorted(other, key=lambda x: x['date']):
    hit = [y['title'][:70] for y in lc if LC_SAME.get(x['id'], '\0') in y['title']]
    print(x['date'], x['id'][:55].ljust(55), 'LastCall:', hit[0] if hit else '-')
print('in Last Call:', sum(1 for x in other if x['id'] in LC_SAME and any(LC_SAME[x['id']] in y['title'] for y in lc)), 'of', len(other))
