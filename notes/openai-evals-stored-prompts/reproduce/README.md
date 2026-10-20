# Reproduce: who still calls OpenAI Evals and stored prompts

Search date: October 20, 2026. Python 3.10 or later, standard library only.

| File | What it is |
|---|---|
| `search-queries.txt` | The 75 GitHub code search queries (three strings, split by language) |
| `counts.json` | Totals behind every number in the note |
| `p-sample-labels.csv` | The 52 labelled stored-prompt files: sample (1 or 2), codebase (anonymised), counted files in that codebase, label |
| `estimate.py` | Computes the codebase-weighted estimate and bootstrap ranges from the labels |
| `SHA256SUMS` | Hashes of the files above |

```sh
sha256sum -c SHA256SUMS
python3 estimate.py
```

`estimate.py` prints, for each sample and both together, the estimate with "unclear" left out
and counted as yes. The pooled "yes only" line is the note's "about 40": 42 (95% range 22–64).

Codebases are anonymised because most real callers are small personal projects. Rerunning the
search will not give the same hits: GitHub's index changes and its counts are approximate.
To check your own code, use the commands in the note.
