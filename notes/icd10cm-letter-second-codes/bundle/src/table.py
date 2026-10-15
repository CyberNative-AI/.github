"""Print the per-tool table from score.json (added after the result; it reads score.json and changes nothing).

Usage: python3 src/table.py score.json
"""
import json
import sys

ARMS = ["QA26", "M26", "QA27", "N27", "DEL27", "OLD", "JUNK"]
d = json.load(open(sys.argv[1], encoding="utf-8"))
print(f"ruling: {d['ruling']}  hits: {', '.join(d['hits']) or 'none'}  tools: {d['n_tools']}  excluded: {d['n_excluded']}")
print("| tool | " + " | ".join(ARMS) + " | class | FY2027 |")
print("|---" * (len(ARMS) + 3) + "|")
for tool, v in sorted(d["tools"].items(), key=lambda kv: (kv[1].get("class", ""), kv[0])):
    if v.get("excluded") == "setup_error":
        print(f"| {tool} | " + " | ".join("-" for _ in ARMS) + " | excluded | - |")
        continue
    cells = [f"{v['arms'][a]['accept']}/{v['arms'][a]['n']}" if a in v["arms"] else "-" for a in ARMS]
    print(f"| {tool} | " + " | ".join(cells) + f" | {v['class']} | {v['fy2027']} |")
