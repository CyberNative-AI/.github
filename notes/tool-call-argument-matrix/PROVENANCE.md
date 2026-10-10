# Provenance

How the files in this directory were produced, for the malformed tool-call argument matrix.

## Inputs

- `source/`, bound by `source/MANIFEST.json` (SHA-256 `00ea7e1a724997dbc46ecb7638c8442352d7f7c8e5011d04df41afe2b5a22dc6`, 16 files). `NOTE.md`, `README.md` and the smolagents report were written from an earlier state of `source/`. Since then only text changed: a doubled word in the docstrings of `drive.py` and `run_one.py`, the last sentence of the Strands caveat in `facts.json`, and the `source_classification` field of `facts.json`. Code behavior, the 162 rows of `cells.jsonl`, counts, versions and pins are unchanged.
- Public upstream pages, read on 2026-10-10:
  - smolagents `v1.26.0` `src/smolagents/{models,agents,tools}.py` from raw.githubusercontent.com, with SHA-256 `e3510666f0a36d1d09d25d9d9f2e9cb0e0c09edc47ed599b0e52445bddf146e7`, `da0da2e258c346e28d97b3584dfe58dcd203fc20fbde6c6533e333f9b1a06352` and `0f7395444c1efa48d0995efacf07bc6b68e5bad75a4312b509604eb447aff5e8`. On `main` (commit `96f33faaf028479119ec8d34507b47694cf14e34`, 2026-10-06) the same three files are byte-identical.
  - The smolagents live `bug_report.md` template and `CONTRIBUTING.md`, and the releases list (newest v1.26.0, 2026-05-29).
  - GitHub issue search, open and closed issues and PRs in `huggingface/smolagents`. Queries and total hits: `parse_json_if_needed` (2); `tool arguments string is:issue` (38); `"invalid JSON" tool arguments` (6); `malformed tool call arguments` (6). We read every title, and the bodies of #294, #404, #991, #992, #1000 and #1775. None reports the parse-failure fallback. #294 and #1000 are related history.
  - Strands #2051 and #4655, and LlamaIndex #16316, are cited by URL from `source/facts.json`. Their status is as recorded there.

## Transformations

- `NOTE.md` matrix table: generated from all 162 rows of `source/cells.jsonl`. The generator asserts 162 rows, nine frameworks and one stable classification per framework/scenario pair, and maps each classification label to short text:

  | label | text |
  |---|---|
  | `executed_intended_arguments` | ran, intended |
  | `executed_other_arguments` | ran, other args |
  | `executed_control_defaults` | ran, defaults |
  | `error_returned_to_model` | error to model |
  | `error_returned_to_caller` | error to caller |
  | `no_execution_no_text_error` | stopped, no text error |
  | `caller_exception` | exception |

- `NOTE.md` and `README.md` prose: every count, version, caveat and limit comes from `source/facts.json`, `source/cells.jsonl` or the source code. Framework-specific source statements are scoped as they are in `facts.json`.
- `README.md` mapping between `analyze.py` classes and `cells.jsonl` labels: read from the class definitions in `source/analyze.py` and the label names. The export step that produced `cells.jsonl` is not in `source/`.
- `smolagents/smolagents-body.md`: follows the live smolagents bug template and was filed as https://github.com/huggingface/smolagents/issues/2951. The fenced Python block is byte-identical to `smolagents/smolagents_repro.py`. The actual output shown is from the execution below.

## New executable code and its execution

- `smolagents/smolagents_repro.py` is company-authored code: a single-parameter tool, `ToolCallingAgent` with `OpenAIServerModel`, and a stub OpenAI-compatible server on 127.0.0.1. Its tool docstring follows `source/run_one.py`.
- It was executed on 2026-10-10 in the existing matrix image, using that image's smolagents environment (smolagents 1.26.0, openai 3.28.0, Python 3.12.15). The run used no network (`--network none`), a read-only mount, CPU, memory and pid limits, `no-new-privileges` and `python -I`. It made no model calls and no rebuild.
- Observed `list_items` arguments: truncated `{"status": "archived"` was passed through as the raw string. Extra brace `{"status": "archived"}}` was passed through as the raw string. Valid `{"status": "archived"}` arrived as `'archived'`. Every run exited with code 0, with no exception and final answer `done`. These match the smolagents `v_trunc`, `v_extra_brace` and `ctl_valid` rows in `source/cells.jsonl`.
- We did not execute it with a fresh `pip install` from PyPI, or on `main`.

## Excluded

Original request logs and bodies, prompts, framework prompt templates, stderr, protocol drafts, review prose, internal identifiers and infrastructure details.

