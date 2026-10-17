"""Show the two differences on one small conversation (run run.py first to fill ./work).

    python demo.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "work/enc-1017/encoding"))
import encoding as enc  # DeepSeek's reference encoder from DeepSeek-V4.1-Flash-1017
from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained(str(HERE / "work/tokenizer"))
TEMPLATES = {"PR #68 template": HERE / "work/pr68/chat_template.jinja",
             "synced template": HERE / "chat_template.jinja"}


def chat(arguments):
    return [
        {"role": "user", "content": "What is the weather in Paris?"},
        {"role": "assistant", "reasoning_content": "I should call get_weather.",
         "tool_calls": [{"id": "c1", "type": "function",
                         "function": {"name": "get_weather", "arguments": arguments}}]},
        {"role": "tool", "tool_call_id": "c1", "content": "18 C, cloudy"},
    ]


def segment(prompt):
    """The rendered assistant tool-call turn: from <｜Assistant｜> to its end-of-sentence token."""
    start = prompt.index("<｜Assistant｜>")
    return prompt[start:prompt.index("<｜end▁of▁sentence｜>", start) + len("<｜end▁of▁sentence｜>")]


def show(title, messages):
    print(f"== {title}")
    ref = enc.encode_messages(json.loads(json.dumps(messages)), thinking_mode="thinking")
    print(f"   encoding.py:\n      {segment(ref)!r}")
    for name, path in TEMPLATES.items():
        out = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True,
                                      thinking_mode="thinking", chat_template=path.read_text(encoding="utf-8"))
        print(f"   {name}: {'same as encoding.py' if out == ref else 'DIFFERENT'}")
        if out != ref:
            print(f"      {segment(out)!r}")


show("1. thinking mode, no tools list, dict arguments", chat({"city": "Paris"}))
show("2. same, OpenAI-style JSON string arguments", chat('{"city": "Paris"}'))
