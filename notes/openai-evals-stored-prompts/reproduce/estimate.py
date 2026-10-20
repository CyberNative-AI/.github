"""Codebase-weighted estimate of active public codebases that call OpenAI stored prompts.

Input: p-sample-labels.csv (two labelled random samples of counted files; codebases anonymised).
Each sampled file is weighted by 1/(counted files in its codebase), so a codebase with many matching
files does not count many times. 95% range: bootstrap over sampled files, 4,000 draws, seed 1.
Usage: python3 estimate.py
"""
import csv, random
from pathlib import Path

COUNTED_CODEBASES = 166  # codebases with at least one counted file (search scanned 2026-10-20)
rows = list(csv.DictReader(open(Path(__file__).with_name("p-sample-labels.csv"), encoding="utf-8")))

def estimate(sample, yes_labels):
    num = sum(1 / int(r["counted_files_in_codebase"]) for r in sample if r["label"] in yes_labels)
    den = sum(1 / int(r["counted_files_in_codebase"]) for r in sample)
    return COUNTED_CODEBASES * num / den

for name, which in (("sample 1", {"1"}), ("sample 2", {"2"}), ("pooled", {"1", "2"})):
    sub = [r for r in rows if r["sample"] in which]
    for rule, yes in (("yes only", {"yes"}), ("unclear counted as yes", {"yes", "unclear"})):
        rng = random.Random(1)
        boot = sorted(estimate([sub[rng.randrange(len(sub))] for _ in sub], yes) for _ in range(4000))
        print(f"{name:8} n={len(sub):2}  {rule:22}  {round(estimate(sub, yes)):3}  (95% range {round(boot[100])}-{round(boot[3900])})")
labels = [r["label"] for r in rows]
print(f"labelled files: {len(rows)}; yes {labels.count('yes')}, no {labels.count('no')}, unclear {labels.count('unclear')}")
