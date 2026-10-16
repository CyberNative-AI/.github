# Reads `rg --json` output; prints file:line where each match starts.
import json, sys
for line in sys.stdin:
    m = json.loads(line)
    if m["type"] != "match": continue
    d = m["data"]; text = d["lines"]["text"]
    for sm in d["submatches"]:
        print(f'{d["path"]["text"]}:{d["line_number"] + text[:sm["start"]].count(chr(10))}')
