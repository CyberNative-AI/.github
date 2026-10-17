"""Random differential: chat_template.jinja vs DeepSeek's reference encoding.py.

    python fuzz.py <template> [n] [seed]     (run.py must have downloaded ./work first)

Generates OpenAI/HF-shaped conversations (system, user text/images, assistant with
reasoning_content and dict-argument tool calls, role "tool" results with text/images,
mid-conversation system messages), renders each with both, and counts mismatches.
"""
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "work/enc-1017/encoding"))
import encoding as enc  # reference encoder of DeepSeek-V4.1-Flash-1017
from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained(str(HERE / "work/tokenizer"))
tok.chat_template = Path(sys.argv[1]).read_text(encoding="utf-8")
N = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
rng = random.Random(int(sys.argv[3]) if len(sys.argv) > 3 else 0)
TOOLS = [{"type": "function", "function": {"name": n, "description": f"tool {n}",
          "parameters": {"type": "object", "properties": {"q": {"type": "string"}, "k": {"type": "integer"}}}}}
         for n in ("lookup", "fetch")]
WORDS = "alpha beta gamma delta 你好 émoji 🙂 x".split()


def text():
    return " ".join(rng.choice(WORDS) for _ in range(rng.randint(1, 4)))


def user():
    if rng.random() < 0.25:
        blocks = [{"type": "text", "text": text()}]
        blocks.insert(rng.randint(0, 1), {"type": "image_url", "image_url": {"url": f"{rng.random():.3f}.png"}})
        return {"role": "user", "content": blocks}
    return {"role": "user", "content": text()}


def conversation():
    msgs = []
    if rng.random() < 0.5:
        msgs.append({"role": "system", "content": text()})
    for turn in range(rng.randint(1, 3)):
        msgs.append(user())
        for step in range(rng.randint(0, 2)):
            calls = [{"id": f"c{turn}{step}{i}", "type": "function",
                      "function": {"name": rng.choice(["lookup", "fetch"]),
                                   "arguments": {"q": text(), "k": rng.randint(0, 9)}}}
                     for i in range(rng.randint(1, 2))]
            a = {"role": "assistant", "content": rng.choice(["", text()]), "tool_calls": calls}
            if rng.random() < 0.7:
                a["reasoning_content"] = text()
            msgs.append(a)
            order = calls[:] if rng.random() < 0.6 else list(reversed(calls))
            for c in order:
                content = text() if rng.random() < 0.7 else [
                    {"type": "text", "text": text()}, {"type": "image_url", "image_url": {"url": "t.png"}}]
                msgs.append({"role": "tool", "tool_call_id": c["id"], "content": content})
        if rng.random() < 0.15:
            msgs.append({"role": "system", "content": text()})
        if turn < 2 and rng.random() < 0.8 and msgs[-1]["role"] != "system":
            a = {"role": "assistant", "content": text()}
            if rng.random() < 0.7:
                a["reasoning_content"] = text()
            msgs.append(a)
    return msgs


mismatch, examples, errors, by_kind = 0, [], 0, {}
for i in range(N):
    msgs = conversation()
    tools = TOOLS if rng.random() < 0.6 else None
    mode = rng.choice(["thinking", "chat"])
    effort = rng.choice([None, 1, 50, 100, "low", "max"])
    kw = {"thinking_mode": mode}
    if effort is not None:
        kw["reasoning_effort"] = effort
    ref_msgs = ([{"role": "system", "content": "", "tools": tools}] if tools else []) + msgs
    if tools and msgs[0]["role"] == "system":
        ref_msgs = [dict(msgs[0], tools=tools)] + msgs[1:]
    try:
        ref = enc.encode_messages(json.loads(json.dumps(ref_msgs)), **kw)
    except Exception as e:
        errors += 1
        continue
    out = tok.apply_chat_template(msgs, tools=tools, tokenize=False, add_generation_prompt=True, **kw)
    kind = f"{mode}, {'tools' if tools else 'no tools'}"
    if out != ref:
        mismatch += 1
        by_kind[kind] = by_kind.get(kind, 0) + 1
        if len(examples) < 3:
            examples.append((i, mode, bool(tools), effort))
print(f"conversations={N} reference_errors={errors} mismatches={mismatch} by_kind={by_kind} first={examples}")
