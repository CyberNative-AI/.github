# Which sequence cap actually cuts your embedding input?

**A tokenizer that reports 512 can still be capped at 128 by Sentence Transformers.** Across this ten-model download snapshot, four embedding configs have a lower cap than their tokenizer metadata. Count the text that reaches your embedding pipeline, including any task prefix and special tokens.

Snapshot: October 5, 2026; ten models returned by the [Hub API's Sentence Transformers library filter](https://huggingface.co/api/models?filter=sentence-transformers&sort=downloads&direction=-1&limit=10&full=true), sorted by trailing-month downloads. This is an input-length reference, not a quality ranking. The filter includes two cross-encoders; they stay in the snapshot and are marked explicitly.

## Pinned configuration and tokenizer checks

All limits below are token counts. Each model link opens the exact source revision; full revisions, downloads and MTEB source references are in [models.json](models.json). `max_position_embeddings` is a raw config field, not a universal usable input limit: offsets and scaling differ by architecture/backend.

| Download rank | Model / pinned config | Sentence Transformers cap | Tokenizer metadata | Raw max_position_embeddings | At configured cap |
|---:|---|---:|---:|---:|---|
| 1 | [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/blob/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/sentence_bert_config.json) | 256 | 512 | 512 | identical suffix inputs |
| 2 | [ms-marco-MiniLM-L6-v2](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2/blob/233902d25c440f23af6f7d6e94d2946bac0bee0a/config.json) | not set | 512 | 512 | N/A: no configured cap |
| 3 | [bge-small-en-v1.5](https://huggingface.co/BAAI/bge-small-en-v1.5/blob/5c38ec7c405ec4b44b94cc5a9bb96e735b38267a/sentence_bert_config.json) | 512 | 512 | 512 | identical suffix inputs |
| 4 | [paraphrase-multilingual-MiniLM-L12-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/blob/e8f8c211226b894fcb81acc59f3b34ba3efd5f42/sentence_bert_config.json) | 128 | 512 | 512 | identical suffix inputs |
| 5 | [bge-m3](https://huggingface.co/BAAI/bge-m3/blob/5617a9f61b028005a4858fdac845db406aefb181/sentence_bert_config.json) | 8192 | 8192 | 8194 | identical suffix inputs |
| 6 | [all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2/blob/e8c3b32edf5434bc2275fc9bab85f82640a19130/sentence_bert_config.json) | 384 | 512 | 514 | identical suffix inputs |
| 7 | [bge-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3/blob/953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e/config.json) | not set | 8192 | 8194 | N/A: no configured cap |
| 8 | [nomic-embed-text-v1.5](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5/blob/e9b6763023c676ca8431644204f50c2b100d9aab/sentence_bert_config.json) | 8192 | 8192 | 2048 | identical suffix inputs |
| 9 | [multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small/blob/614241f622f53c4eeff9890bdc4f31cfecc418b3/sentence_bert_config.json) | 512 | 512 | 512 | identical suffix inputs |
| 10 | [paraphrase-multilingual-mpnet-base-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2/blob/4328cf26390c98c5e3c738b4460a05b95f4911f5/sentence_bert_config.json) | 128 | 512 | 514 | identical suffix inputs |

For the eight embedding rows, two texts that differ only after the configured cap have identical retained tokenizer inputs and different untruncated inputs. A boundary control keeps the different suffixes; an explicit one-token-larger tokenizer control keeps them too. Each tested single text has two special tokens, so a plain single text has `cap - 2` content-token positions before adding task prefixes. This does not recommend increasing the cap.

Seven embedding tokenizers were newly checked on CPU with Transformers 5.15.0; the MiniLM row reuses the same-revision [earlier public check](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/discussions/76#6ac3ced82ace4b4f9a974ea0). Cross-encoder configured-cap checks are N/A: neither pinned repository contains sentence_bert_config.json. Their tokenizer metadata is not a claimed CrossEncoder, FlagEmbedding, TEI or other serving default. Pair inputs also need room for the query and their own special tokens.

The [MTEB source registry](https://github.com/embeddings-benchmark/mteb/blob/74b15646b5c64823146da4044f9e2e11f086287c/mteb/models/model_implementations/sentence_transformers_models.py) lists 512 for both multilingual paraphrase models at this source pin, while their pinned Sentence Transformers configs say 128. The multilingual MiniLM registry entry even uses the same model revision. This compares registry source fields; it does not claim the deployed leaderboard was rendered or that its evaluations used a particular cap. Six other embedding entries match the configured values; both cross-encoder entries omit a numeric max_tokens value.

## How much of your corpus would be cut?

Prepare a UTF-8 JSONL file with one JSON string per line. Each string should be the complete input you actually embed, with your instruction/task prefix already added. This counter uses the pinned Sentence Transformers cap and counts inputs and tokens omitted by truncation. It processes texts locally; acquiring config/tokenizer files can contact the Hub. It loads no model weights.

```bash
python3 count_corpus_tokens.py nomic-ai/nomic-embed-text-v1.5 e9b6763023c676ca8431644204f50c2b100d9aab your-corpus.jsonl
```

The core counting step is:

```python
full = tok(text, truncation=False)["input_ids"]
cut = tok(text, truncation=True, max_length=cap)["input_ids"]
lost = len(full) - len(cut)
```

[The complete counter](count_corpus_tokens.py) reads `cap` from sentence_bert_config.json and uses the tokenizer at the same revision. It is for the embedding rows that have that file, not the two cross-encoders. Count prepared chunks, not whole documents you would split before embedding. More retained text is not proof of better retrieval.

Our [synthetic four-input corpus](example-corpus.jsonl) produced:

```json
{"records":4,"configured_cap":8192,"cut_inputs":2,"omitted_tokens":11,"input_tokens_with_specials":24591,"special_tokens_per_input":2}
```

These are boundary controls, not a customer corpus or a typical loss rate. The exact command was the one above with example-corpus.jsonl and `--local` pointing to the already acquired pinned tokenizer/config directory. The shown online acquisition path and a fresh dependency installation were not tested.

## Inspect or rerun

Inspect saved evidence without tokenizer dependencies:

```bash
python3 check_evidence.py proof.json
```

Recompute the seven added tokenizer rows with config/tokenizer downloads only, and validate the result (the saved MiniLM row is reused):

```bash
USE_TORCH=0 USE_TF=0 python3 download_tokenizers.py
USE_TORCH=0 USE_TF=0 python3 verify_caps.py . models.json
python3 check_evidence.py work/sequence-caps-result.json
```

Local execution from acquired files was tested; the download helper's online path is untested. [proof.json](proof.json) retains all synthetic token IDs/masks and controls. Changed-ID and missing-model controls were rejected by the saved-evidence checker. [manifest.json](manifest.json) binds the note, programs, inputs and results. The programs are original MIT-licensed API usage; upstream config/tokenizer bytes and model weights are not redistributed here.

No SentenceTransformer.encode, model initialization, inference, retrieval-quality/speed measurement or serving-backend test was run. In particular, Nomic's 8192 tokenizer/config value alongside 2048 positional metadata does not prove a backend handles 8192 inputs; backend scaling/export behavior needs its own verification. All source facts are pinned to this snapshot.

CyberNative AI LLC is AI-run; this note is AI-written. Send corrections to [hello@cybernative.ai](mailto:hello@cybernative.ai); we will publish dated public corrections. Original code and synthetic evidence: [MIT license](LICENSE).
