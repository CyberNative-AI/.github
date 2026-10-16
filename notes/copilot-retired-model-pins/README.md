# From November 16, a Copilot agent pinned to a retired model runs on another model, with no error

GitHub retires Claude Opus 4.8, Claude Opus 5 and GPT-5.6 Terra from all Copilot experiences on November 16, 2026 ([changelog, October 15](https://github.blog/changelog/2026-10-15-upcoming-deprecation-of-selected-github-copilot-models-in-mid-november)). Individual subscribers on annual plans keep Claude Opus 4.8. GitHub suggests Claude Opus 5.5 in place of both Opus models and GPT-6.1 Sol or GPT-6 Luna in place of GPT-5.6 Terra, and asks users to "update your workflows and integrations". The changelog does not say what happens to a custom agent or prompt file whose `model:` names one of these models.

We read the VS Code 1.142.0 source (October 14, commit `d956e8a6`) to find out:

- **When you select the agent in chat,** VS Code tries each name in `model:` in order. If none is available, it writes one warning to the log and keeps the model already in the model picker. The agent's instructions and tools still apply. ([`chatInputPart.ts` 1417–1428](vscode-1.142.0/chatInputPart-L1417-1428.ts.txt))
- **In the agent or prompt file,** the editor marks the name "Unknown model '…' will be ignored." as a hint, which shows as faded text. It is not a warning or an error. ([`promptValidator.ts` 424–433](vscode-1.142.0/promptValidator-L424-433.ts.txt))
- **When another agent calls it as a subagent,** the subagent runs on the main chat's model. VS Code's own unit test checks this case: "keeps main model when configured subagent model is unavailable". ([`runSubagentTool.ts` 586–610](vscode-1.142.0/runSubagentTool-L586-610.ts.txt), [test](vscode-1.142.0/runSubagentTool.test-L927-949.ts.txt))

So a review agent pinned to `Claude Opus 5 (copilot)` will, from November 16, run on whatever model the picker holds, or on whatever model the calling agent uses. The log line and the faded hint are the only signals.

## How many public files pin one

On October 16, 2026, GitHub code search found **555 files** in `.github/agents`, `.github/prompts` and `.github/chatmodes` whose frontmatter `model:` names one of the three models. They are in 174 public repositories under 122 owners, including 11 repositories owned by Microsoft organizations. In **387 files (132 repositories)**, every listed model is one of the three, so VS Code has nothing else in the list to fall back to.

| Model | Files that name it in `model:` | Files with no other model listed |
|---|---:|---:|
| Claude Opus 4.8 | 349 | 253 |
| Claude Opus 5 | 78 | 49 |
| GPT-5.6 Terra | 132 | 86 |

Files that list two retiring models count in both rows. Of the files with no other model listed, the 253 that include Claude Opus 4.8 keep working for individual annual-plan subscribers. Code search indexes only default branches, skips forks and returns at most 1,000 results per query, so these are lower bounds. Agents kept in a VS Code user profile are not in any repository and are not counted.

## Find yours

From the repository root:

```sh
git grep -nE 'Claude Opus (4\.8|5)([^.0-9]|$)|GPT-5\.6 Terra' -- .github
```

The pattern matched all 555 files above, plus 63 that mention one of the names only in text ([`results/grep-check.json`](results/grep-check.json)). Only `model:` lines and the list items under them matter. It skips Claude Opus 5.5. Output from three of the public repositories is in [`results/git-grep-3-repos.txt`](results/git-grep-3-repos.txt).

## Fix

VS Code uses the first listed model that is available, so put a model that stays first:

```yaml
model: ['Claude Opus 5.5 (copilot)', 'GPT-6.1 Sol (copilot)']
```

An individual on an annual plan who wants to keep Claude Opus 4.8 can list it first. Anyone who no longer has it gets the next entry:

```yaml
model: ['Claude Opus 4.8 (copilot)', 'Claude Opus 5.5 (copilot)']
```

VS Code matches a name exactly, including case: for Copilot models, either the display name or `Name (copilot)`. Copy the name from the model picker. After you save, the faded hint should not appear on any entry.

## Method and limits

- **Read from source, not run.** We did not run this in a Copilot session. The behaviour comes from the 1.142.0 source and the VS Code unit test named above. The same logic is on `main` at `2de3870e` (October 16).
- **Prompt files:** 29 of the 555 files are prompt files (`.prompt.md`). They get the same editor hint, but they run through a different code path that we did not trace. The behaviour above is for agents, including the 3 legacy chat mode files.
- **Other Copilot surfaces are not covered.** In the Agents window and other agent-host sessions, an open VS Code issue ([microsoft/vscode#338949](https://github.com/microsoft/vscode/issues/338949)) reports that the pinned model is ignored even when it is available. We did not test Copilot CLI or the coding agent on GitHub.com. Agent files written for those surfaces sometimes use IDs such as `claude-opus-4.8`, which the pattern above does not match.
- **Counts:** `scripts/count.py collect` runs the three code searches in `results/summary.json` and downloads each file. `scripts/count.py summarize` reads the frontmatter and counts only files where `model:` names a retiring model. That rule covers a single value, an inline array (also over several lines) and a block list. A file counts as having no other model when every listed name is one of the three, as a display name or a model ID such as `claude-opus-4.8`; we did not check whether the other names listed in the remaining files still exist. `scripts/grep_check.py` runs the grep pattern over the same files. Search totals changed between result pages in our run.
- **Excerpts:** the files in `vscode-1.142.0/` are quoted from VS Code, Copyright (c) Microsoft Corporation, MIT License ([`LICENSE.txt`](vscode-1.142.0/LICENSE.txt)).

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai.
