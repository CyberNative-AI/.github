#!/usr/bin/env python3
"""Count a pinned Qwen text prompt, including the tool instructions it emits.

Synthetic demonstration only. No model weights or tool execution are required.
Copyright 2026 CyberNative AI LLC. SPDX-License-Identifier: MIT
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

from transformers import AutoTokenizer

REVISION = "017b9c7af6b5689d5dd426a76e0bc077eb5ca20a"
MODEL = "Qwen/Qwen3.8-27B-FP8"
HASHES = {
    "tokenizer.json": "0997f410c57a1f4e53b09e4be8f4a172d90edd9564368fb0847030937229b9f3",
    "tokenizer_config.json": "b11349aafa7cdc6a320767cf7ceb29ed82f7eda5d65e8e0819e76f0ce947bf27",
    "chat_template.jinja": "c3cf9e34abf4f9e36c2d72165aa9c132d3e2a725b6c2586aaa3a8af9d7a81041",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def tool(index):
    return {
        "type": "function",
        "function": {
            "name": f"lookup_order_{index:02}",
            "description": "Return the current status of the supplied order ID.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
                "additionalProperties": False,
            },
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    for name, expected in HASHES.items():
        if sha((args.source_dir / name).read_bytes()) != expected:
            raise ValueError(f"Source hash mismatch: {name}")
    tokenizer = AutoTokenizer.from_pretrained(
        args.source_dir, local_files_only=True, trust_remote_code=False
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    messages = [{"role": "user", "content": "Check order A-100's status."}]

    def render(tools):
        options = dict(tools=tools, add_generation_prompt=True, enable_thinking=False)
        text = tokenizer.apply_chat_template(messages, tokenize=False, **options)
        ids = tokenizer(text, add_special_tokens=False).input_ids
        direct_ids = tokenizer.apply_chat_template(
            messages, tokenize=True, return_dict=False, **options
        )
        if ids != direct_ids:
            raise ValueError("Rendered prompt and direct template IDs disagree")
        return text, ids

    baseline_text, baseline_ids = render(None)
    if render([]) != (baseline_text, baseline_ids):
        raise ValueError("Empty tool-list control differs from absent tools")
    rows = []
    for count in (0, 1, 4, 8):
        tools = [tool(i) for i in range(1, count + 1)]
        text, ids = render(tools)
        schema_ids = []
        if count:
            if text.count("<tools>") != 1 or text.count("</tools>") != 1:
                raise ValueError("Unexpected tool envelope")
            schema = text.split("<tools>\n", 1)[1].split("\n</tools>", 1)[0]
            schema_ids = tokenizer(schema, add_special_tokens=False).input_ids
        prefix = args.output_dir / f"tools-{count}"
        prefix.with_suffix(".txt").write_text(text, encoding="utf-8")
        prefix.with_suffix(".ids.json").write_text(json.dumps(ids) + "\n")
        increment = len(ids) - len(baseline_ids)
        rows.append({
            "tools": count,
            "prompt_tokens": len(ids),
            "increment_over_no_tools": increment,
            "schema_only_tokens": len(schema_ids),
            "increment_minus_schema_only": increment - len(schema_ids),
            "prompt_sha256": sha(text.encode("utf-8")),
            "ids_sha256": sha(json.dumps(ids).encode("utf-8")),
        })
    changed = tool(1)
    changed["function"]["description"] += " This is a synthetic sensitivity control."
    if render([changed])[1] == render([tool(1)])[1]:
        raise ValueError("Changed description did not change prompt IDs")
    result = {
        "model": MODEL, "revision": REVISION, "source_hashes": HASHES,
        "versions": {p: importlib.metadata.version(p) for p in
                     ("transformers", "tokenizers", "jinja2")},
        "messages": messages, "enable_thinking": False,
        "add_generation_prompt": True, "rows": rows,
        "controls": {"empty_tools_equal_absent": True,
                     "direct_template_ids_equal_rendered_ids": True,
                     "changed_description_changes_ids": True},
    }
    output = json.dumps(result, indent=2) + "\n"
    (args.output_dir / "result.json").write_text(output)
    print(output, end="")


if __name__ == "__main__":
    main()
