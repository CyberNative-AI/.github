#!/usr/bin/env python3
"""Exercise pinned upstream functions on synthetic input. No model or API client."""
import argparse
import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.request import urlopen

import pandas as pd
from anyascii import anyascii

REVISION = 'a96232870bdb0bd763f0131320e8377c6deb575e'
ROOT = f'https://raw.githubusercontent.com/allenai/ai2-scholarqa-lib/{REVISION}/'
SOURCES = {
    'prompt_utils.py': ('api/scholarqa/lite/prompt_utils.py', '31a3556c222c40f6245ee54711e4036f93e7b24eb35ba6867daab27d0f91b40f'),
    'prompts.py': ('api/scholarqa/llms/prompts.py', 'f71c9a9cfd6684ebd946bdd12b4048143ce70852e5ded0c653cd32c62b06ed7a'),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='New directory for source, input and prompt receipts')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    sources = {}
    for filename, (path, expected_hash) in SOURCES.items():
        with urlopen(ROOT + path, timeout=30) as response:
            raw = response.read(100_001)
        if len(raw) > 100_000 or hashlib.sha256(raw).hexdigest() != expected_hash:
            raise RuntimeError(f'Source size/hash mismatch: {filename}')
        (args.out / filename).write_bytes(raw)
        sources[filename] = ast.parse(raw.decode('utf-8'), filename=filename)

    template = None
    for node in sources['prompts.py'].body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'UNIFIED_GENERATION_PROMPT' for t in node.targets):
            template = ast.literal_eval(node.value)
    if not isinstance(template, str):
        raise RuntimeError('Expected a literal upstream prompt template')

    names = ['normalize_snippet_quote', 'prepare_references_data', 'build_prompt']
    functions = [n for n in sources['prompt_utils.py'].body if isinstance(n, ast.FunctionDef) and n.name in names]
    if [n.name for n in functions] != names or any(n.decorator_list for n in functions):
        raise RuntimeError('Unexpected upstream function selection')
    namespace = {'pd': pd, 'anyascii': anyascii, 'json': json, 'Any': Any, 'Dict': Dict, 'List': List, 'Tuple': Tuple, 'UNIFIED_GENERATION_PROMPT': template}
    # The selected function ASTs are unchanged. Only package initialization is excluded.
    exec(compile(ast.Module(body=functions, type_ignores=[]), 'pinned-upstream-functions', 'exec'), namespace)

    snippets_key = '[91000001 | Fixture A | 2025 | Citations: 0]'
    abstract_key = '[91000002 | Fixture B | 2025 | Citations: 0]'
    empty_key = '[91000003 | Fixture C | 2025 | Citations: 0]'
    methods = 'Synthetic methods: the evaluation used one toy dataset.'
    result = 'Synthetic result: accuracy improved only on that dataset.'
    abstract = 'Synthetic abstract: a retrieval method is proposed; no experiment is reported.'
    records = [
        {'reference_string': snippets_key, 'sentences': [{'text': result, 'char_offset': 200, 'section_title': 'results'}, {'text': methods, 'char_offset': 100, 'section_title': 'methods'}], 'abstract': 'Synthetic abstract not selected because snippets are present.'},
        {'reference_string': abstract_key, 'sentences': [], 'abstract': abstract},
        {'reference_string': empty_key, 'sentences': [], 'abstract': ''},
    ]
    (args.out / 'input.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    references, per_paper, metadata = namespace['prepare_references_data'](pd.DataFrame(records))
    expected = {snippets_key: methods + ' ' + result, abstract_key: abstract}
    if references != expected or set(per_paper) != set(expected) or set(metadata) != set(expected):
        raise RuntimeError('Reference/metadata result differs from the declared fixture')
    if metadata[abstract_key][0]['section_title'] != 'abstract':
        raise RuntimeError('Abstract metadata was not preserved')
    prompt = namespace['build_prompt']('What evidence supports the proposed method?', references)
    block = re.search(r'<section_references>\s*(.*?)\s*</section_references>', prompt, re.DOTALL)
    if not block or json.loads(block.group(1)) != expected:
        raise RuntimeError('Prompt references differ from formatter output')
    (args.out / 'prompt.txt').write_text(prompt, encoding='utf-8')
    receipt = {'source_revision': REVISION, 'input_records': len(records), 'reference_records': len(references), 'snippets_in_document_order': True, 'abstract_fallback': True, 'empty_evidence_omitted': empty_key not in references, 'prompt_references_match': True, 'model_inference': False, 'retrieval_executed': False, 'references': references}
    rendered = json.dumps(receipt, indent=2) + '\n'
    (args.out / 'receipt.json').write_text(rendered, encoding='utf-8')
    print(rendered, end='')


if __name__ == '__main__':
    main()
