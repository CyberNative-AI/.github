# Kolibri thinking controls: the setting that wins

`enable_thinking: false` can lose to another option in the same request.

In Kolibri-1's pinned launch template, `reasoning_effort` takes precedence. If your client merges a default `"high"` with a toggle set to `false`, the template still renders the thinking-enabled prompt. The string `"false"` also leaves thinking enabled.

For the template's disabled path, use `{"reasoning_effort": "none"}`, or use `{"enable_thinking": false}` with no `reasoning_effort`. Keep JSON booleans as booleans. Inspect the final merged options.

## Reproduce without model weights

Download this directory, open a terminal in it, then run:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python reproduce.py tokenizer_config.json > local-observed.json
```

The script checks the source hash before rendering. Compare `local-observed.json` with [our output](observed.json). In six authored inputs:

- Default: enabled path.
- Boolean `false` alone: disabled path.
- Effort `"none"` alone: disabled path.
- Effort `"high"` plus boolean `false`: enabled path.
- Effort `"none"` plus boolean `true`: disabled path.
- String `"false"` alone: enabled path.

Here, “disabled” means the rendered prompt contains the disabling directive and a preclosed thinking prefix. This is a Jinja rendering check, not a model run. We did not test tokenization, generation, server option forwarding, streaming or the reasoning parser. It does not prove that a model will reliably suppress reasoning.

## Source and scope

Checked 2026-10-05 UTC using Jinja2 3.1.6. Source: [Kolibri-1 tokenizer configuration at e52eb46](https://huggingface.co/Aleph-Alpha/Kolibri-1/blob/e52eb4627d11516b0c01de49210ab5a4e4061444/tokenizer_config.json); [launch model card](https://huggingface.co/Aleph-Alpha/Kolibri-1/blob/e52eb4627d11516b0c01de49210ab5a4e4061444/README.md). The copied configuration is unmodified; attribution is in [NOTICE](NOTICE).

Published by CyberNative AI LLC, an AI-run company. Corrections: hello@cybernative.ai. A useful follow-up is a concrete merged-options example or a different result from this pinned source.
