#!/usr/bin/env python3
"""Render a pinned Kolibri template. No model or tokenizer execution."""
# Copyright 2026 CyberNative AI LLC. Licensed under Apache-2.0.

import argparse
import hashlib
import json
from pathlib import Path

import jinja2
from jinja2.sandbox import SandboxedEnvironment


REVISION = "e52eb4627d11516b0c01de49210ab5a4e4061444"
SOURCE_SHA256 = "876849ec94a65a6b72e3fd1c8d37cc00db9892d4fd84279eb51602ea06cd1b46"
CASES = [
    ("default", {}, False),
    ("boolean_false", {"enable_thinking": False}, True),
    ("effort_none", {"reasoning_effort": "none"}, True),
    ("high_and_false", {"reasoning_effort": "high", "enable_thinking": False}, False),
    ("none_and_true", {"reasoning_effort": "none", "enable_thinking": True}, True),
    ("string_false", {"enable_thinking": "false"}, False),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Pinned tokenizer_config.json")
    args = parser.parse_args()
    source = args.source.read_bytes()
    digest = hashlib.sha256(source).hexdigest()
    if digest != SOURCE_SHA256:
        raise SystemExit("Source SHA256 mismatch; no result produced.")
    config = json.loads(source)
    template = SandboxedEnvironment().from_string(config["chat_template"])
    rows = []
    for name, options, expected_disabled in CASES:
        prompt = template.render(
            messages=[{"role": "user", "content": "Name one weekday."}],
            tools=[],
            add_generation_prompt=True,
            **options,
        )
        disabled_directive = "Reasoning is disabled." in prompt
        suffix = prompt.rsplit("<|im_start|>assistant\n", 1)[1]
        closed_prefix = suffix == "<think>\n\n</think>\n\n"
        if disabled_directive != expected_disabled or closed_prefix != expected_disabled:
            raise SystemExit(f"Unexpected render in {name}; no result produced.")
        rows.append({
            "case": name,
            "options": options,
            "disabled_directive": disabled_directive,
            "closed_think_prefix": closed_prefix,
            "assistant_prefix_after_role": suffix,
            "rendered_prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        })
    print(json.dumps({
        "revision": REVISION,
        "source_sha256": digest,
        "jinja2_version": jinja2.__version__,
        "scope": "Jinja template rendering only; no tokenizer, model or server",
        "cases": rows,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
