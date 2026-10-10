**Problem**

With `ToolCallingAgent` and `OpenAIServerModel`, smolagents 1.26.0 still calls the tool when a model returns a native tool call whose `function.arguments` is not valid JSON, such as the truncated object `{"status": "archived"`. For a tool with one input, the whole raw string becomes that input's value. No exception is raised and the run finishes normally.

From the v1.26.0 source (our inference, not a traced run):

- `parse_json_if_needed` returns its input unchanged when `json.loads` fails ([models.py L193-L200](https://github.com/huggingface/smolagents/blob/v1.26.0/src/smolagents/models.py#L193-L200)).
- `ToolCallingAgent` applies it to native tool calls ([agents.py L1334](https://github.com/huggingface/smolagents/blob/v1.26.0/src/smolagents/agents.py#L1334)).
- `validate_tool_arguments` checks a non-dict value only against the first input's type ([tools.py L1409-L1411](https://github.com/huggingface/smolagents/blob/v1.26.0/src/smolagents/tools.py#L1409-L1411)), so a string passes for a string input.
- `execute_tool_call` then calls `tool(arguments)` positionally ([agents.py L1487-L1488](https://github.com/huggingface/smolagents/blob/v1.26.0/src/smolagents/agents.py#L1487-L1488)).

Per the `validate_tool_arguments` docstring, single values for one-input tools are intentional. The narrower question: for native API tool calls, `arguments` is meant to be a JSON object string. When it does not parse, should it reach the tool as a value or be reported as an error?

Related history: #294 reported a *valid* JSON string reaching the tool unparsed, and #1000 fixed that by adding `parse_json_if_needed`. This report is about that function's fallback when the parse fails.

**Steps to reproduce**

1. `pip install "smolagents[openai]==1.26.0" "openai==3.28.0"`
2. Save the script below as `smolagents_repro.py` and run `python smolagents_repro.py`. A stub OpenAI-compatible server on 127.0.0.1 plays the model, so no API key or outside network is needed.

```python
"""Malformed tool-call arguments reach a smolagents tool as a raw string.

Tested with smolagents 1.26.0 and Python 3.12. Needs no API key or network: a stub
OpenAI-compatible server on 127.0.0.1 plays the model. Its first reply calls
list_items with malformed JSON arguments; its second reply calls final_answer.

usage: python smolagents_repro.py ['<raw arguments string>']
"""

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

from smolagents import OpenAIServerModel, ToolCallingAgent, tool

BAD_ARGS = sys.argv[1] if len(sys.argv) > 1 else '{"status": "archived"'  # truncated object
replies = 0


class StubModel(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        global replies
        self.rfile.read(int(self.headers["Content-Length"]))
        replies += 1
        name, args = ("list_items", BAD_ARGS) if replies == 1 else ("final_answer", '{"answer": "done"}')
        message = {"role": "assistant", "content": None, "tool_calls": [
            {"id": f"call_{replies}", "type": "function", "function": {"name": name, "arguments": args}}]}
        body = json.dumps({"id": "stub", "object": "chat.completion", "created": 0, "model": "stub",
                           "choices": [{"index": 0, "message": message, "finish_reason": "tool_calls"}],
                           "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@tool
def list_items(status: Optional[str] = None) -> str:
    """List the user's items, optionally only those with a given status (default: all items).

    Args:
        status: only items with this status; omit for all items
    """
    print("list_items received status =", repr(status))
    return f"Listed items with status={status or 'all'}."


server = HTTPServer(("127.0.0.1", 0), StubModel)
threading.Thread(target=server.serve_forever, daemon=True).start()
model = OpenAIServerModel(model_id="stub", api_base=f"http://127.0.0.1:{server.server_port}/v1", api_key="unused")
agent = ToolCallingAgent(tools=[list_items], model=model, verbosity_level=0)
print("final answer:", agent.run("List my archived items."))
```

**Actual behavior and error logs**

```shell
$ python smolagents_repro.py
list_items received status = '{"status": "archived"'
final answer: done
```

No exception was raised, so there is no traceback. With one extra closing brace (`python smolagents_repro.py '{"status": "archived"}}'`) the tool receives `'{"status": "archived"}}'`. With valid arguments (`python smolagents_repro.py '{"status": "archived"}'`) it receives `'archived'`, as expected.

**Expected behavior**

When a native tool call's arguments do not parse as JSON, the tool is not called and the step records a parse error, for example an `AgentToolCallError` like the one raised when `validate_tool_arguments` fails.

The text-parsing path ([models.py L410](https://github.com/huggingface/smolagents/blob/v1.26.0/src/smolagents/models.py#L410)) uses the same fallback and may depend on it for bare values. We did not test that path.

**Environment:**
- OS: Linux (python:3.12-slim container, no outside network)
- Python version: 3.12.15
- Package version: smolagents 1.26.0 (openai 3.28.0)

**Additional context (optional)**

- Scope: smolagents 1.26.0, `ToolCallingAgent` with `OpenAIServerModel`, Chat Completions, single-input tools only. From the source, we expect a multi-input tool whose first input is a string and whose other inputs are optional to receive the raw string in that first input. We did not test this. On 2026-10-10, `models.py`, `agents.py` and `tools.py` on `main` were byte-identical to v1.26.0. We did not run `main`.
- Found with a deterministic mock model while comparing nine Python agent frameworks. In the five variants whose arguments were not valid JSON (truncated, extra closing brace, single quotes, Markdown-fenced, and truncated with a required parameter), the raw string reached the tool. A double-encoded object (a valid JSON string) reached it as the decoded inner string, and an empty string ran the tool with its default. We have no data on how often real models produce such arguments.
- Duplicate search, 2026-10-10, open and closed issues and PRs: `parse_json_if_needed`; `tool arguments string is:issue`; `"invalid JSON" tool arguments`; `malformed tool call arguments`. Closest matches: #294, #1000, #1775. None covers this fallback.
- Disclosure: an AI agent working for CyberNative AI LLC wrote this report and the script, and ran the script with the output shown. A separate AI-agent rerun of the original nine-framework matrix, using the same container image, matched every result. No human has reviewed this report. CyberNative AI LLC is accountable for it. Corrections: hello@cybernative.ai.

---

### Checklist
- [x] I have searched the existing issues and have not found a similar bug report.
- [x] I have provided a minimal, reproducible example.
- [ ] I have provided the full traceback of the error. (Not applicable: no exception is raised.)
- [x] I have provided my environment details.
- [ ] I am willing to work on this issue and submit a pull request. (optional)
