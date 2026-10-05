#!/usr/bin/env python3
"""Inspect pinned input guards and tokenizer arguments; never load model weights."""
import ast
import hashlib
import json
from types import SimpleNamespace
from urllib.request import urlopen

REPO = "perplexity-ai/pplx-embed-v2-context-9b-preview"
REV = "b667039ee8b438a6350fbc91bbcecd86f9d363ba"
SOURCE_SHA256 = "090f68c9907f2b055b3f41bd0dfc94ef8250e8a98e390e6d308b8fa34702bd45"
CONFIG_SHA256 = "8f0ee5fd8901b88b779ec0f094c60db04ca59fcf9b831c420bab325aa5a51236"


def fetch(name, expected):
    url = f"https://huggingface.co/{REPO}/resolve/{REV}/{name}"
    with urlopen(url, timeout=30) as response:
        data = response.read(32_769)
    if len(data) > 32_768 or hashlib.sha256(data).hexdigest() != expected:
        raise RuntimeError(f"Pinned source check failed: {name}")
    return data


class ModelBoundary(Exception):
    pass


class TokenizerBoundary(Exception):
    pass


class Capture:
    def __call__(self, texts, **kwargs):
        self.texts = texts
        self.kwargs = kwargs
        raise TokenizerBoundary


def main():
    source = fetch("modeling_pplx_contextual.py", SOURCE_SHA256)
    config = json.loads(fetch("config.json", CONFIG_SHA256))
    tree = ast.parse(source)
    original = next(n for n in tree.body
                    if isinstance(n, ast.ClassDef) and n.name == "PplxContextualModel")
    names = {"encode", "encode_queries", "prepare_inputs"}
    methods = [n for n in original.body
               if isinstance(n, ast.FunctionDef) and n.name in names]
    if {n.name for n in methods} != names:
        raise RuntimeError("Expected methods missing")
    # Preserve all three function bodies. Omit only encode's inference decorator,
    # the model base class, imports and initialization. Stop before either external
    # operation. This is source inspection with callable boundary probes.
    for method in methods:
        method.decorator_list = []
    module = ast.Module(body=[
        ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
        ast.ClassDef(name="Probe", bases=[], keywords=[], body=methods, decorator_list=[]),
    ], type_ignores=[])
    namespace = {}
    exec(compile(ast.fix_missing_locations(module), "<pinned-methods>", "exec"), namespace)
    Probe = namespace["Probe"]

    def stop_at_model(self):
        raise ModelBoundary

    Probe.eval = stop_at_model
    probe = Probe()
    probe.config = SimpleNamespace(**config)
    probe.tokenizer = Capture()
    outcomes = []

    def expect(label, call, exception, message=None):
        try:
            call()
        except exception as error:
            if message is not None and str(error) != message:
                raise AssertionError(f"Unexpected exception text: {label}") from error
            outcomes.append(label)
        else:
            raise AssertionError(f"Unexpected result: {label}")

    shape_error = "Expected a list of documents, each a list of text chunks"
    expect("flat document batch rejected", lambda: probe.encode(["first", "second"]), TypeError, shape_error)
    expect("flat query batch rejected", lambda: probe.encode_queries(["question"]), TypeError, shape_error)
    expect("nested document batch passes early guards", lambda: probe.encode([["first", "second"]]), ModelBoundary)
    expect("nested query batch passes early guards", lambda: probe.encode_queries([["question"]]), ModelBoundary)
    expect("multi-chunk query rejected before tokenization", lambda: probe.prepare_inputs([["first", "second"]], "query"), ValueError, "Each query must contain exactly one string")
    expect("unsupported task rejected", lambda: probe.encode([["first"]], task="other"), ValueError, "Unsupported task: other")
    expect("zero batch size rejected", lambda: probe.encode([["first"]], batch_size=0), ValueError, "batch_size must be positive")

    probe.encode = lambda documents, **kwargs: (documents, kwargs)
    routed_documents, routed_options = probe.encode_queries([["question"]])
    assert routed_documents == [["question"]] and routed_options == {"task": "query"}
    del probe.encode

    def capture(documents, task):
        expect(f"{task} tokenizer boundary reached",
               lambda: probe.prepare_inputs(documents, task), TokenizerBoundary)
        assert probe.tokenizer.kwargs["truncation"] is False
        return probe.tokenizer.texts

    grouped = capture([["first", "second"]], "document")
    separate = capture([["first"], ["second"]], "document")
    queries = capture([["question"]], "query")
    assert grouped == [config["document_prefix"] + "first" + config["boundary_marker"] + "second"]
    assert separate == [config["document_prefix"] + "first", config["document_prefix"] + "second"]
    assert queries == ["question"]
    print(json.dumps({
        "revision": REV,
        "passed_boundary_probes": len(outcomes),
        "grouped_document_tokenizer_texts": grouped,
        "separate_document_tokenizer_texts": separate,
        "query_tokenizer_texts_before_prefix_token": queries,
        "encode_queries_forwarded_task": routed_options["task"],
        "scope": "early guards and tokenizer arguments only; no tokenizer, tensors, weights or embeddings",
    }, indent=2))


if __name__ == "__main__":
    main()
