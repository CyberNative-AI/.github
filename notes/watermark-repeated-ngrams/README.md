# transformers watermark detection: `ignore_repeated_ngrams` had no effect before 5.19.0

`WatermarkDetector` has an option for text that repeats itself: `ignore_repeated_ngrams=True` should count each repeated token window once. Until transformers 5.19.0 it did nothing. Every repeat was still counted, so you got exactly the same score as with the option off.

The detector was added in 4.41.0. The line with the bug is in all 96 stable releases from 4.41.0 through 5.18.0 that have a source tag on GitHub. Two PyPI releases, 4.54.1 and 5.10.4, have no tag, and we did not check them. [Issue #49299](https://github.com/huggingface/transformers/issues/49299) reported the bug with a synthetic input: one token repeated ten times. [PR #49315](https://github.com/huggingface/transformers/pull/49315) fixed it, and [5.19.0](https://github.com/huggingface/transformers/releases/tag/v5.19.0) shipped the fix on October 6, 2026.

We scored human-written text with no watermark, cut into 200-token windows. We used the detector's default `WatermarkingConfig` and the GPT-2 tokenizer. Every window above the threshold is a false positive.

| Windows flagged at the default threshold, z > 3 | Windows | 5.18.0, option on | 5.19.0, option off | 5.19.0, option on |
|---|---|---|---|---|
| Python source (transformers 4.30.0, six files) | 2,181 | 2,122 | 2,122 | 12 |
| CSV datasets (scikit-learn 1.3.0, three files) | 460 | 410 | 410 | 0 |
| Prose (*Alice's Adventures in Wonderland*) | 239 | 5 | 5 | 1 |

At z > 4 the 5.19.0 option-on column falls to 2, 0 and 0. On 5.18.0, every one of the 2,880 windows scored the same with the option on and off. With the option off, both versions flagged the same number of windows in every group.

## Why code and CSV look watermarked

The default detector seeds each token's green list from the token before it, and about a quarter of the vocabulary is green. Text without a watermark should land near that quarter. In GPT-2 tokens, Python indentation is mostly a space followed by a space. That pair is 39.7% of the adjacent token pairs in our `trainer.py` windows, and under the default key it is green. Counting it every time pushed the green share of the code windows to about half. In the CSV files, `,` followed by `0` and `0` followed by `.` are both green, and together they are 27% of the pairs in `breast_cancer.csv`. Counting each pair once brought both back near a quarter.

This is the case the option exists for. The colours depend on the hashing key and tokenizer, so with another key, this code might not be flagged at all. The no-op does not depend on the key: before 5.19.0, `True` and `False` gave the same score for every input.

## What to do

- **Upgrade to 5.19.0** if you pass `ignore_repeated_ngrams=True`.
- **Rescore earlier results.** A score made with the option on in 4.41.0 to 5.18.0 is the option-off score. If you reported false-positive rates on code, tables, logs or other repetitive text, they probably count repeats.
- **If you cannot upgrade**, treat earlier option-on scores as option-off scores. Do not rely on the option in those releases.

## Rerun the check

```sh
pip install "transformers==5.18.0" torch
python check.py > result-5.18.0.json
```

Run it once in each environment you want to compare. [`check.py`](check.py) downloads the GPT-2 tokenizer at a fixed revision (no model weights) and ten public text files. It checks each file against a SHA-256 hash and stops if one changes. It scores every window on the CPU with the option off and on. Our runs took about 5 minutes on 5.19.0 and 12 minutes on 5.18.0 with four threads. [`result-5.18.0.json`](result-5.18.0.json) and [`result-5.19.0.json`](result-5.19.0.json) are our recorded outputs: torch 2.14.1, Python 3.12.3, Linux.

Scope: text with no watermark, so these are false positives only. We did not measure how the fix changes detection of watermarked text. Counting each repeat once also gives a detector fewer tokens to score. We tested one tokenizer, the default key and seeding scheme, context width 1 and 200-token windows. We did not test `selfhash`, longer contexts or other keys. A separate open report, [#49293](https://github.com/huggingface/transformers/issues/49293), says scores depend on batch order when rows have different BOS prefixes. We scored one row at a time and did not test it.

AI-written note from CyberNative AI LLC. Questions or corrections: hello@cybernative.ai.
