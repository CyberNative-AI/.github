# AstaBrief: check the evidence going into the report

A paper can be in your corpus and absent from the report writer's evidence. Check that boundary before judging the prose.

[Ai2 released AstaBrief on October 2](https://allenai.org/blog/astabrief): an open model that writes a cited scientific report from a question and retrieved literature excerpts. For a developer adapting it to a curated corpus, the useful first inspection is the reference block handed to the writer.

## A small example you can inspect

In [the linked library's reference formatter](https://github.com/allenai/ai2-scholarqa-lib/blob/a96232870bdb0bd763f0131320e8377c6deb575e/api/scholarqa/lite/prompt_utils.py), records with snippets use those snippets in document order. A record without snippets falls back to its abstract. A record with neither contributes no reference text. This function accepts prepared records; it does not open PDFs.

Our [recipe](reproduce.py) exercises that formatter and its prompt builder with three explicitly synthetic records:

- A record with two out-of-order snippets supplies both in document order. Its abstract is not selected.
- An abstract-only record supplies the abstract, with abstract metadata.
- An empty record supplies nothing.

The result is two references from three input records. The recipe also checks that the prompt's reference block contains exactly that result. It preserves the input, downloaded source, prompt and receipt so you can inspect what crossed this boundary.

## Run the example

Download [reproduce.py](reproduce.py) and [requirements.txt](requirements.txt) into a new working directory. With [uv](https://docs.astral.sh/uv/getting-started/installation/) and an existing Python installation:

```sh
uv venv --no-config --no-python-downloads .venv
uv pip install --no-config --no-cache --python .venv/bin/python \
  --index-url https://pypi.org/simple -r requirements.txt
.venv/bin/python reproduce.py --out proof
```

`proof` must not already exist. Setup downloads Python dependencies; the recipe downloads two public source files at the pinned revision and verifies their SHA-256 hashes. It runs three unchanged function bodies extracted from that source, using real pandas and anyascii dependencies. It reads the literal prompt template without initializing the full ScholarQA package. Tested on Linux with CPython 3.10.19 and uv 0.10.7; other environments are untested.

Open `proof/input.json`, `proof/prompt.txt` and `proof/receipt.json`. The reference JSON inside `<section_references>` is the concrete evidence to inspect. In your own integration, distinguish full-text snippets from abstract-only records, and investigate relevant documents that supplied no evidence before asking the writer to synthesize them.

## What this establishes

This is a source-slice demonstration, not an installed ScholarQA application or an AstaBrief report. It runs no retrieval or model inference and measures no speed, report quality or citation accuracy. It establishes no offline or private deployment property. The library revision is pinned for reproducibility; we do not identify it as the model's release commit.

The [release's evaluation caveat](https://allenai.org/blog/astabrief) also matters: most training and evaluation took place in 2025, and Ai2 has not repeated the full comparison against current frontier models. A citation's presence still does not establish that the attached claim preserves the source's scope.

Published by CyberNative AI LLC. Prepared with AI assistance; source and execution limits are stated above. Corrections: hello@cybernative.ai. The downloaded upstream source is [Apache-2.0 licensed](https://github.com/allenai/ai2-scholarqa-lib/blob/a96232870bdb0bd763f0131320e8377c6deb575e/LICENSE); it is not bundled here.
