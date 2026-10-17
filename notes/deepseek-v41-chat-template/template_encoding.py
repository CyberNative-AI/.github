"""Stand-in for DeepSeek's encoding module that renders prompts with a chat_template.jinja.

DeepSeek's test_encoding.py does `import encoding`. This module re-exports the reference
encoder (imported as `_ref_encoding`) and replaces encode_messages/encode_case so every
prompt the tests check comes from transformers' apply_chat_template instead. Validation
errors and image lists still come from the reference, so only the prompt text is tested.

Environment: DS_TOKENIZER (dir with tokenizer.json + tokenizer_config.json),
DS_TEMPLATE (template path), DS_DICT_ARGS=1 to pass tool-call arguments as dicts.
"""
import copy
import json
import os

from _ref_encoding import *  # noqa: F401,F403
import _ref_encoding as _ref
from transformers import AutoTokenizer

_tok = AutoTokenizer.from_pretrained(os.environ["DS_TOKENIZER"])
_tok.chat_template = open(os.environ["DS_TEMPLATE"], encoding="utf-8").read()
_DICT_ARGS = os.environ.get("DS_DICT_ARGS") == "1"


def _prepare(msgs):
    msgs = copy.deepcopy(list(msgs))
    if _DICT_ARGS:
        for m in msgs:
            for tc in m.get("tool_calls") or []:
                f = tc.get("function", tc)
                if isinstance(f.get("arguments"), str):
                    try:
                        f["arguments"] = json.loads(f["arguments"])
                    except ValueError:
                        pass
    return msgs


def _render(msgs, **kw):
    return _tok.apply_chat_template(_prepare(msgs), tokenize=False, add_generation_prompt=True, **kw)


def encode_messages(messages, thinking_mode, context=None, drop_thinking=True,
                    add_default_bos_token=True, reasoning_effort=None,
                    return_multi_modal_data=False):
    ref = _ref.encode_messages(messages, thinking_mode, context=context,
                               drop_thinking=drop_thinking,
                               add_default_bos_token=add_default_bos_token,
                               reasoning_effort=reasoning_effort,
                               return_multi_modal_data=True)
    kw = dict(thinking_mode=thinking_mode, drop_thinking=drop_thinking)
    if reasoning_effort is not None:
        kw["reasoning_effort"] = reasoning_effort
    prompt = _render(list(context or []) + list(messages), **kw)
    if context:
        # The reference returns only the text after the context; strip the
        # template's own rendering of the context the same way.
        prefix = _render(context, **kw)
        assert prompt.startswith(prefix), "template context rendering is not a prefix"
        prompt = prompt[len(prefix):]
    elif not add_default_bos_token and prompt.startswith(_tok.bos_token):
        prompt = prompt[len(_tok.bos_token):]
    return (prompt, ref[1]) if return_multi_modal_data else prompt


def encode_case(case, thinking_mode):
    prompt, media = encode_messages(case["messages"],
                                    thinking_mode=case.get("thinking_mode") or thinking_mode,
                                    context=case.get("context"),
                                    reasoning_effort=case.get("reasoning_effort"),
                                    return_multi_modal_data=True)
    return prompt, media["images"]
