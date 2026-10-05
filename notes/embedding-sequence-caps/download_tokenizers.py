"""Download only the pinned config and tokenizer files used by the cap check."""
import json
from pathlib import Path

from huggingface_hub import snapshot_download


def main():
    root = Path(__file__).resolve().parent
    models = json.loads((root / "models.json").read_text())
    for model in models["rows"][1:]:
        snapshot_download(model["repo"], revision=model["revision"],
                          local_dir=root / "sources" / model["repo"].replace("/", "--"),
                          allow_patterns=["config.json", "sentence_bert_config.json",
                                          "tokenizer_config.json", "tokenizer.json",
                                          "special_tokens_map.json", "vocab.txt"])
    (root / "work").mkdir(exist_ok=True)


if __name__ == "__main__":
    main()
