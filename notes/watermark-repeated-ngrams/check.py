"""Does WatermarkDetector(ignore_repeated_ngrams=True) ignore repeated n-grams?

Scores human-written text that carries no watermark with the installed
transformers release. Every non-overlapping 200-token window is scored twice:
ignore_repeated_ngrams=False and =True. Any window above the z threshold is a
false positive.

    pip install "transformers==5.18.0" torch   # or the release you use
    python check.py > result-5.18.0.json

Needs network access the first time: the GPT-2 tokenizer (no model weights)
and ten public text files, each checked against a SHA-256 below. CPU only.
"""

import collections
import hashlib
import json
import platform
import sys
import urllib.request

import torch
import transformers
from transformers import AutoTokenizer, GPT2Config, WatermarkDetector, WatermarkingConfig

TF = "https://raw.githubusercontent.com/huggingface/transformers/v4.30.0/src/transformers/"
SK = "https://raw.githubusercontent.com/scikit-learn/scikit-learn/1.3.0/sklearn/datasets/data/"
CORPUS = [
    # (name, kind, url, sha256)
    ("alice.txt", "prose", "https://www.gutenberg.org/cache/epub/11/pg11.txt", "01b38ea4c710a84bc18d0bd41271a5a1a92b94e97b2812f4dece97d4a694725e"),
    ("modeling_utils.py", "code", TF + "modeling_utils.py", "0431850b4ac6f57c0694c8ddee54c1f84e13b1f8ad9d09fb0747e677be222640"),
    ("trainer.py", "code", TF + "trainer.py", "7925a24e2041c9475507d5e0fe7627cbbe6e334b8c6ea2bc223d25a64e80ebea"),
    ("modeling_bert.py", "code", TF + "models/bert/modeling_bert.py", "21dab0886c7b8c4635a3f57e9d4b15e9b075ac1ca3edf2dace44ee240d9b93b8"),
    ("modeling_t5.py", "code", TF + "models/t5/modeling_t5.py", "24f1561e578366b4fcba19f67dc9ab1deb6bc558b34a18aabe109216a842a08f"),
    ("generation_utils.py", "code", TF + "generation/utils.py", "15b9129ab878a16cdd813e34df5fcf1bb62780f7e5e48be5ac41938956184b31"),
    ("tokenization_utils_base.py", "code", TF + "tokenization_utils_base.py", "c7125cda5b54289acd2f569646bf5e049c3b20cdc9dc12782c8cdd7c79dc5052"),
    ("iris.csv", "csv", SK + "iris.csv", "f13ffa8fdd56fd8e6c8d16d4081a3fbd3114bcd0aae4256c43205169cd9d1449"),
    ("wine_data.csv", "csv", SK + "wine_data.csv", "10e8a802908b34f86e5da8ce962f3c806694bc98450a18f61851af59f324bede"),
    ("breast_cancer.csv", "csv", SK + "breast_cancer.csv", "fed3eb72d0575ef6192293f5093c6e801b1476b577d0386bf4455504522172ed"),
]
TOKENIZER = ("openai-community/gpt2", "607a30d783dfa663caf39e06633721c8d4cfcd7e")
WINDOW = 200
THRESHOLDS = (3.0, 4.0)  # 3.0 is the detector's default


def fetch(url, sha256):
    data = urllib.request.urlopen(url, timeout=60).read()
    got = hashlib.sha256(data).hexdigest()
    if got != sha256:
        sys.exit(f"{url}: SHA-256 {got}, expected {sha256}")
    return data.decode("utf-8")


def main():
    torch.set_num_threads(4)
    tok = AutoTokenizer.from_pretrained(TOKENIZER[0], revision=TOKENIZER[1])
    wcfg = WatermarkingConfig()  # defaults: lefthash, context_width 1, greenlist_ratio 0.25
    detectors = {
        ignore: WatermarkDetector(
            model_config=GPT2Config(), device="cpu", watermarking_config=wcfg, ignore_repeated_ngrams=ignore
        )
        for ignore in (False, True)
    }
    counts = collections.defaultdict(collections.Counter)
    highest = []
    for name, kind, url, sha256 in CORPUS:
        text = fetch(url, sha256)
        if name == "alice.txt":  # drop the Project Gutenberg header and licence
            text = text.split("*** START OF THE PROJECT GUTENBERG EBOOK")[1]
            text = text.split("*** END OF THE PROJECT GUTENBERG EBOOK")[0]
        ids = tok(text)["input_ids"]
        for start in range(0, len(ids) - WINDOW + 1, WINDOW):
            x = torch.tensor([ids[start : start + WINDOW]], dtype=torch.long)
            z = {ignore: float(d(x, return_dict=True).z_score[0]) for ignore, d in detectors.items()}
            for key in (kind, "all"):
                c = counts[key]
                c["windows"] += 1
                c["same_z_with_and_without_ignore"] += abs(z[True] - z[False]) < 1e-9
                for t in THRESHOLDS:
                    c[f"flagged_z>{t}_ignore_False"] += z[False] > t
                    c[f"flagged_z>{t}_ignore_True"] += z[True] > t
            highest.append((z[True], z[False], name, start))
    highest.sort(reverse=True)
    print(json.dumps({
        "transformers": transformers.__version__,
        "torch": torch.__version__,
        "python": platform.python_version(),
        "tokenizer": "@".join(TOKENIZER),
        "watermarking_config": wcfg.to_dict(),
        "window_tokens": WINDOW,
        "counts": {k: dict(v) for k, v in counts.items()},
        "highest_z_ignore_True": [
            {"file": n, "token_offset": s, "z_ignore_True": round(a, 2), "z_ignore_False": round(b, 2)}
            for a, b, n, s in highest[:5]
        ],
    }, indent=1))


if __name__ == "__main__":
    main()
