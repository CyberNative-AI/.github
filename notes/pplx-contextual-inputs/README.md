# Perplexity contextual embeddings: keep the document boundary

Keep a document's chunks together, and send queries through `encode_queries`. A flat batch familiar from sentence encoders is not the input format of `pplx-embed-v2-context-9b-preview`.

For a RAG integration, these inputs describe different documents:

```python
one_document = [["first", "second"]]       # two chunks from one document
two_documents = [["first"], ["second"]]   # two independent documents
queries = [["question"]]                  # one string per query row
```

The pinned [model card](https://huggingface.co/perplexity-ai/pplx-embed-v2-context-9b-preview/blob/b667039ee8b438a6350fbc91bbcecd86f9d363ba/README.md) documents `encode` for document chunks and `encode_queries` for queries. Preserve those roles when adapting an existing embedding wrapper. The card warns that this preview's embeddings should not be mixed with a future release's embeddings.

## Check the input contract without loading weights

Download [reproduce.py](./reproduce.py) and run it with Python 3.12 (tested here on 3.12.3):

```sh
python3 reproduce.py
```

No packages or model weights are installed. The script fetches two small files from the pinned public checkpoint, checks their SHA256 digests, and extracts three methods. It omits the model base, initialization, imports and inference decorator; the method bodies stay unchanged. A substitute `eval` stops execution before model work. A recording substitute tokenizer stops before tokenization and captures its input strings.

Our Python 3.12.3 run on October 5, 2026 reached the expected boundary in all ten guard/tokenizer probes. The recorded text inputs were:

```text
one_document   -> ["[D] first<|chunk_sep|>second"]
two_documents  -> ["[D] first", "[D] second"]
queries        -> ["question"]  (before adding the query prefix token)
```

The wrapper probe also recorded `encode_queries` forwarding `task="query"`. Flat document and query batches raised the input-shape error; a two-string query row failed before tokenization. Nested inputs passed the early guards. That last result does not mean the complete model call succeeded.

This makes the integration check concrete: retain each chunk's original document grouping, use one string per query row, and route queries through the query entry point. If a wrapper merges independent documents, splits every chunk into its own document, or sends queries through the document method, correct that mapping before embedding a corpus.

## What this check leaves open

This is a source-method probe with authored strings and substitute boundaries, not real tokenization, tensor preparation, inference or retrieval evaluation. It produces no vectors and measures no speed, quality or memory use. It does not establish that a particular framework integration works. Only the pinned revision below was checked; later source or interface changes require a new check.

Source inspected October 5, 2026: [implementation](https://huggingface.co/perplexity-ai/pplx-embed-v2-context-9b-preview/blob/b667039ee8b438a6350fbc91bbcecd86f9d363ba/modeling_pplx_contextual.py) and [configuration](https://huggingface.co/perplexity-ai/pplx-embed-v2-context-9b-preview/blob/b667039ee8b438a6350fbc91bbcecd86f9d363ba/config.json), revision `b667039ee8b438a6350fbc91bbcecd86f9d363ba`. The checkpoint declares MIT; its fetched source remains upstream material. This original note and probe are [MIT licensed](./LICENSE).

Prepared with AI assistance by CyberNative AI LLC. Corrections: hello@cybernative.ai.
