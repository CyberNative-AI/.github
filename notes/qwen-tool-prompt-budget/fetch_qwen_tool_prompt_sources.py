#!/usr/bin/env python3
"""Download three pinned public tokenizer files, without weights.

Copyright 2026 CyberNative AI LLC. SPDX-License-Identifier: MIT
"""
import argparse
import hashlib
from pathlib import Path
from urllib.request import urlopen

REVISION = "017b9c7af6b5689d5dd426a76e0bc077eb5ca20a"
HASHES = {
    "tokenizer.json": "0997f410c57a1f4e53b09e4be8f4a172d90edd9564368fb0847030937229b9f3",
    "tokenizer_config.json": "b11349aafa7cdc6a320767cf7ceb29ed82f7eda5d65e8e0819e76f0ce947bf27",
    "chat_template.jinja": "c3cf9e34abf4f9e36c2d72165aa9c132d3e2a725b6c2586aaa3a8af9d7a81041",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, expected in HASHES.items():
        path = args.output_dir / name
        if path.exists():
            data = path.read_bytes()
        else:
            url = f"https://huggingface.co/Qwen/Qwen3.8-27B-FP8/resolve/{REVISION}/{name}"
            with urlopen(url, timeout=30) as response:
                data = response.read(20_000_001)
        if len(data) > 20_000_000 or hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f"Source size/hash check failed: {name}")
        path.write_bytes(data)
        print(f"verified {name}")


if __name__ == "__main__":
    main()
