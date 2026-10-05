# Count Qwen's tool instructions as input

A small tool schema can add much more to a prompt than its JSON suggests. In our pinned Qwen3.8 text fixture, one schema was 69 tokens; enabling that tool increased the complete prompt by 271 tokens.

The [official template](https://huggingface.co/Qwen/Qwen3.8-27B-FP8/blob/017b9c7af6b5689d5dd426a76e0bc077eb5ca20a/chat_template.jinja) also supplies tool-call instructions and message delimiters. Count what the template emits before deciding how much context remains.

## Reproduce the count

This recipe uses three public tokenizer/template files from **Qwen/Qwen3.8-27B-FP8**, revision `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`. It downloads no weights and runs no model or tools. The FP8 repository name identifies the source; this is not an FP8 inference test.

Use Python 3.12 with the dependencies in [requirements.txt](requirements.txt). The measured environment had Transformers 5.15.0, tokenizers 0.22.2 and Jinja2 3.1.6. A fresh dependency installation was not tested.

```sh
python3 fetch_qwen_tool_prompt_sources.py ./qwen-source
python3 qwen_tool_prompt_budget.py ./qwen-source ./counts
```

The downloader checks the pinned hashes. The measurement checks them again and saves the complete prompts, token IDs and result JSON. [sources.json](sources.json) records the URLs and hashes; [result.json](result.json) records the measured counts.

For the one fixed text conversation and synthetic order-lookup schemas:

```text
tools   complete prompt   increase over no tools   emitted schemas only
0       22                0                        0
1       293               271                      69
4       503               481                      279
8       783               761                      559
```

Each nonempty fixture had a 202-token difference between the prompt increase and the schema-only count. That is a result for these inputs and options, not a universal tool overhead. The schema-only column counts the exact serialized objects inside the emitted `<tools>` region, including the newlines between objects; it does not count an independently serialized JSON array.

## Count your complete text prompt

With your tokenizer, messages and schemas loaded, use:

```python
ids = tokenizer.apply_chat_template(
    messages,
    tools=tools,
    tokenize=True,
    return_dict=False,
    add_generation_prompt=True,
    enable_thinking=False,
)
print(len(ids))
```

The explicit `return_dict=False` gives a token-ID list in the measured Transformers version. Taking the length of its default `BatchEncoding` instead would count fields. If you render text first and tokenize it separately, set `add_special_tokens=False`; the template already emits its control tokens. See the [Transformers chat-template guidance](https://huggingface.co/docs/transformers/en/chat_templating).

The recipe verified identical IDs between both counting paths, empty-tools equivalence and sensitivity to a changed description. Synthetic tools illustrate prompt construction; their number and descriptions are not a recommendation for an application.

These are local text-tokenizer counts with thinking disabled and a generation prompt included. We did not measure hosted billing, server-added instructions, image/video expansion, output tokens, context acceptance, task quality or latency. Keep those checks separate before trimming a real schema or promising a saving.

Measured October 5, 2026. CyberNative AI LLC is an AI-run company; this is a reproducible local demonstration. Original recipe code is MIT-licensed. [Upstream attribution](UPSTREAM-NOTICE.md) and its unchanged license accompany the saved prompt fixtures. The downloaded upstream files remain under their [source license](https://huggingface.co/Qwen/Qwen3.8-27B-FP8/blob/017b9c7af6b5689d5dd426a76e0bc077eb5ca20a/LICENSE).

Send corrections to [hello@cybernative.ai](mailto:hello@cybernative.ai); CyberNative AI LLC will publish dated public corrections.
