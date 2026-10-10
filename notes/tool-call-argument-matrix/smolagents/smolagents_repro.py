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
