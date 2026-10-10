# Reproducing the malformed tool-call argument matrix

This explains how to rebuild and rerun the nine-framework grid behind `NOTE.md`, and how to read the published per-cell data. Start with `NOTE.md` for the findings. Everything runs offline against a scripted mock model, with no API key and no paid calls.

## Files

| file | role |
|---|---|
| `source/Dockerfile`, `source/req-*.txt` | `python:3.12-slim` image with one virtual environment per framework, pinned to exact versions on 2026-10-09 |
| `source/mock_llm.py` | OpenAI-compatible Chat Completions mock. Its first reply calls the tool with the scenario's raw arguments; every later reply is `Done.` |
| `source/run_one.py` | Runs one framework at default settings. Only the endpoint, a dummy key and the model name are configured. The tools log the exact arguments they received |
| `source/drive.py` | Runs the grid: scenarios x frameworks x replicates, 120 s per cell |
| `source/analyze.py` | Frozen classifier and decision rule |
| `source/cells.jsonl` | Published per-cell results: 162 rows, every framework, scenario and replicate, including controls |
| `source/facts.json` | Versions, scenarios, counts, caveats and limits |
| `smolagents/smolagents_repro.py` | Standalone smolagents reproduction. `smolagents/smolagents-body.md` is the report filed as [huggingface/smolagents#2951](https://github.com/huggingface/smolagents/issues/2951) |
| `MANIFEST.json`, `source/MANIFEST.json` | SHA-256 and byte count of every file |
| `PROVENANCE.md` | Inputs, transformations and exclusions |

## Rerun the grid

From the directory that contains this README:

```
docker build -t toolcall-matrix source/
mkdir out
docker run --rm --network none --cpus 4 --memory 6g --memory-swap 6g --pids-limit 1024 \
  --security-opt no-new-privileges -v "$PWD/source":/w:ro -v "$PWD/out":/out toolcall-matrix \
  python /w/drive.py /out ctl_valid,ctl_empty_obj,v_trunc,v_extra_brace,v_empty,v_single_quote,v_double_enc,v_fenced,r_trunc all 2
docker run --rm --network none -v "$PWD/source":/w:ro -v "$PWD/out":/out toolcall-matrix python /w/analyze.py /out
```

- The build needs network access to install the pinned packages. The pins are exact versions, not hashes, so wheels built on another date may differ. This packet's results come from a single image build, which we did not rebuild for this packet.
- `drive.py` writes `cells.jsonl`, `tools.jsonl` and `requests.jsonl` to `out/`, and resumes from them if they already exist.
- `analyze.py` writes `results.json` and `cells-classified.jsonl`, and prints the decision and the matrix.
- `requests.jsonl` stores full request bodies, including each framework's own prompt templates. Those templates belong to their projects and fall under their licenses. We do not publish them.

## Classifier and decision rule (frozen before the main run)

`analyze.py` classifies each cell from the tool log, the outcome and the text the framework sent back after the first tool call:

| `analyze.py` class | label in `source/cells.jsonl` | meaning |
|---|---|---|
| `EXEC_INTENDED` | `executed_intended_arguments` | tool ran with exactly the intended arguments |
| `SILENT_WRONG` | `executed_other_arguments` | tool ran with any other arguments |
| `EXEC_DEFAULT` | `executed_control_defaults` | `{}` control ran with defaults |
| `RAISE` | `caller_exception` | an exception reached the caller |
| `MODEL_ERROR` | `error_returned_to_model` | error-like text was sent back to the model |
| `CALLER_ERROR` | `error_returned_to_caller` | the final output carries error-like text |
| `DROP_SILENT` | `no_execution_no_text_error` | no tool run, no exception, no error-like text |

- A framework counts only if its valid control runs with the intended arguments in both replicates; all 9 did.
- A framework counts toward the ruling if, on either core variant (`v_trunc`, `v_extra_brace`), both replicates are `SILENT_WRONG` or `DROP_SILENT`.
- Fewer than 6 valid frameworks: INVALID. Otherwise, at least 3 counting on a core variant: CONTINUE. At least 3 on any malformed variant: CHANGE. Else: STOP. The result was 5 on the core variants, so CONTINUE.
- `v_empty` is reported but not counted.

The classifier reads only text. LangChain and Google ADK expose the error in structured fields (`invalid_tool_calls`, `MALFORMED_FUNCTION_CALL`) but send no error text back, so they are `DROP_SILENT`. Counting those fields as visible gives 3 instead of 5. `NOTE.md` reports both numbers.

## Published data

`source/cells.jsonl` is a derived export of the checked raw outputs. Each row contains framework, scenario, replicate, classification, terminal outcome, model request count, whether streaming was used, and the tool invocations with their exact arguments. It does not contain request bodies, prompts, framework prompt templates, final text or stderr. Our export step is not part of this packet. A rerun produces the raw files above, which `analyze.py` classifies directly.

## Evidence status

Artifact checked. AI agents built and ran the experiment. A separate AI-agent rerun from the same image, on the same machine, matched all 162 cells. This is not independent scientific reproduction or replication. Please send corrections or a reproduction on another setup to hello@cybernative.ai.

Company-authored harness code: CyberNative AI LLC, under the Apache License 2.0 (`LICENSE`, `NOTICE`). The frameworks under test are third-party projects under their own licenses.

AI-written note from CyberNative AI LLC. Questions or corrections: hello@cybernative.ai.
