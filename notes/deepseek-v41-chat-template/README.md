# DeepSeek-V4.1-Flash-1017 ships without a chat template, and the one in V4.1-Flash no longer matches DeepSeek's encoder

DeepSeek published [DeepSeek-V4.1-Flash-1017](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017) on 17 October
2026. Its README says the release "does not include a Jinja-format chat template". With transformers,
`apply_chat_template` on its tokenizer raises
`ValueError: Cannot use chat template functions because tokenizer.chat_template is not set`.

The obvious move is to borrow the template from
[DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash). That repository has had a
`chat_template.jinja` since a community
[pull request 68](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/discussions/68) was merged on 1 October. The 1017 repository has the same
`config.json`, `tokenizer_config.json` and `encoding/` folder, byte for byte. We checked whether that template still
produces the same prompts as DeepSeek's own encoder (`encoding/encoding.py`).

**Short answer: not since 16 October.** That day DeepSeek changed `encoding.py` ("fix(encoding): preserve tool image
order and current-turn thinking"), and 1017 ships the changed version. Against it, the template fails 4 of the 55 tests
in DeepSeek's own `encoding/test_encoding.py`. A two-part edit of the template passes all 55. Separately, and since the
template was added, tool-call arguments must be passed as dicts, not as OpenAI-style JSON strings.

| template | DeepSeek tests, encoder of 1 Oct | DeepSeek tests, encoder of 16 Oct (= 1017) | random conversations, differ from the 1017 encoder |
|---|---:|---:|---:|
| V4.1-Flash `chat_template.jinja` (PR 68) | 50/50 | 51/55 | 322 of 3,000 |
| [`chat_template.jinja`](chat_template.jinja) in this folder | 50/50 | 55/55 | 0 of 9,000 |

Tests use dict arguments; [`results/run-output.txt`](results/run-output.txt) also has the string-argument runs.

## What differs

**1. Reasoning from earlier tool steps of the current turn (thinking mode, no `tools` list).** Since 16 October the
encoder keeps the model's reasoning for every step of the turn still in progress, including steps that called a tool;
it drops reasoning only from finished turns. The PR 68 template treats each tool result as the start of a new turn, so
it drops that reasoning. This happens only when the request has tool calls in its history but no `tools` list, for
example a final request sent without tools to force an answer. When `tools` is passed, both keep all reasoning and
agree. All 322 differing random conversations were in thinking mode with no `tools` list.

```
encoding.py      <｜Assistant｜><think>I should call get_weather.</think>\n\n<｜DSML｜ calls>...
PR #68 template  <｜Assistant｜></think>\n\n<｜DSML｜ calls>...
```

**2. Tool results given as `content_blocks`.** DeepSeek's encoder also accepts its own `content_blocks` field on user
and tool messages. The template ignored it: tool results inside a user message's `content_blocks` were left out, and a
tool message's came out as an empty `<tool_result></tool_result>`. This accounts for 3 of the 4 failing tests. The PR
68 template already rendered ordinary `{"role": "tool", "content": ...}` messages, including ones with image parts,
the same as the encoder.

**3. Older, and not fixed here: pass arguments as dicts.** With OpenAI-style arguments (`"arguments": "{\"city\": \"Paris\"}"`),
both templates render each earlier call as one parameter named `arguments` that holds the JSON text. The encoder parses
the JSON and writes one parameter per argument:

```
encoding.py      <｜DSML｜ parameter name="city" string="true">Paris</｜DSML｜ parameter>
both templates   <｜DSML｜ parameter name="arguments" string="true">{"city": "Paris"}</｜DSML｜ parameter>
```

A Jinja template cannot parse JSON text, so convert the arguments with `json.loads` before rendering. With string
arguments, both templates fail 9 of 50 tests against the 1 October encoder. Against the 16 October and 1017 encoders,
the original template fails 13 of 55 and the synced template fails 9 of 55.

## What to use

- If you can call Python, DeepSeek's own [`encoding/encoding.py`](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017/blob/main/encoding/encoding.py)
  or its [deepseek-recipe](https://github.com/deepseek-ai/deepseek-recipe) libraries are the reference; the 1017 README
  points to deepseek-recipe for production use.
- If your stack needs a Jinja template, use [`chat_template.jinja`](chat_template.jinja) from this folder (diff against
  PR 68: [`template.diff`](template.diff)). With transformers:

  ```python
  from pathlib import Path
  from transformers import AutoTokenizer

  tok = AutoTokenizer.from_pretrained("deepseek-ai/DeepSeek-V4.1-Flash-1017")
  tok.chat_template = Path("chat_template.jinja").read_text(encoding="utf-8")
  prompt = tok.apply_chat_template(messages, tools=tools, tokenize=False,
                                   add_generation_prompt=True, thinking_mode="thinking")
  ```

  Servers that take a template file (for example vLLM's `--chat-template`) can use the same file. We tested it only
  through transformers 5.20.1 with Jinja2 3.1.6, not in other template engines.
- Either way, pass tool-call arguments as dicts.

## Check it yourself

These commands download and execute DeepSeek's Python code on your machine: `run.py` runs the downloaded tests and
imports the encoder; `fuzz.py` and `demo.py` also import that encoder. Review the pinned code first and use a disposable
isolated environment without credentials or private data.

```sh
python -m pip install "transformers==5.20.1" "pytest==9.*"
python run.py                          # DeepSeek's tests, both templates, three encoder revisions
python fuzz.py chat_template.jinja 3000 1
python fuzz.py work/pr68/chat_template.jinja 3000 1
python demo.py                         # the two examples above
```

`run.py` downloads pinned files into `./work`: the tokenizer and `encoding/` folder of DeepSeek-V4.1-Flash-1017 at
`1bae0e10`, DeepSeek-V4.1-Flash's `encoding/` folder at `2cba9e42` (1 October, when the template was merged) and
`314113f8` (16 October), and the PR 68 template. It then runs DeepSeek's unmodified `test_encoding.py`, with
[`template_encoding.py`](template_encoding.py) standing in for `encoding.py`: prompts come from
`apply_chat_template`; validation errors and image lists still come from DeepSeek's encoder, so only prompt text is
compared. When a test passes earlier messages as context, both sides return only the text after the context.
[`fuzz.py`](fuzz.py) builds random OpenAI/HF-shaped conversations (system and user messages, images, assistant reasoning,
one or two dict-argument tool calls per step, tool results in or out of call order, mid-conversation system messages,
thinking and chat modes, reasoning effort) and compares the two renderings byte for byte; seeds 1, 2 and 3 for this folder's template and seed 1 for the PR 68
template are in [`results/fuzz-output.txt`](results/fuzz-output.txt).

## What we did not do

We did not run the model; at 763B parameters (Hugging Face's count) it is beyond our hardware. This note is about prompt
text only: we make no claim about how much the dropped reasoning changes the model's answers. We did not test
llama.cpp, SGLang or other servers, or whether a given server converts string arguments to dicts before rendering. The
random conversations cover the shapes listed above, not every field the encoder accepts.

[`chat_template.jinja`](chat_template.jinja) and [`template.diff`](template.diff) are modified from the template in
DeepSeek-V4.1-Flash, which is under the MIT License, Copyright (c) 2023 DeepSeek; see
[`chat_template.LICENSE`](chat_template.LICENSE). Checked on 17 October 2026.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. We publish dated corrections when errors are
confirmed. Corrections: hello@cybernative.ai.
