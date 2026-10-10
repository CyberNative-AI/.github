"""Scripted OpenAI-compatible mock model for the tool-call argument matrix (malformed tool-call arguments).

URL: http://127.0.0.1:PORT/r/<run_id>/<scenario>/v1/chat/completions
Turn 1 (no tool result or error text yet in the conversation): call the target tool with the
scenario's raw `arguments` string. Every later turn: final answer. Deterministic; every
request body is logged to a JSONL file.
"""
from __future__ import annotations

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOG_LOCK = threading.Lock()
COUNTS: dict[str, int] = {}
CEILING = 20  # requests per run id; beyond this HTTP 400

# scenario -> (tool name, raw arguments string). Intended action is always status="archived" / city="Paris".
SCENARIOS: dict[str, tuple[str, str]] = {
    "ctl_valid": ("list_items", '{"status": "archived"}'),
    "ctl_empty_obj": ("list_items", "{}"),
    "v_trunc": ("list_items", '{"status": "archived"'),
    "v_empty": ("list_items", ""),
    "v_extra_brace": ("list_items", '{"status": "archived"}}'),
    "v_single_quote": ("list_items", "{'status': 'archived'}"),
    "v_double_enc": ("list_items", json.dumps('{"status": "archived"}')),
    "v_fenced": ("list_items", '```json\n{"status": "archived"}\n```'),
    "r_trunc": ("get_weather", '{"city": "Paris"'),
}
ANSWER = "Done."


def _tool_names(body: dict) -> list[str]:
    out = []
    for t in body.get("tools") or []:
        fn = t.get("function") or t
        if fn.get("name"):
            out.append(fn["name"])
    return out


def _first_turn(body: dict) -> bool:
    msgs = body.get("messages") or []
    for m in msgs:
        if m.get("role") == "tool":
            return False
        if m.get("role") == "assistant" and (m.get("tool_calls") or m.get("content")):
            return False
    return True


def decide(scenario: str, body: dict, seq: int) -> dict:
    names = _tool_names(body)
    cid = f"call_{seq:04d}"
    if _first_turn(body):
        name, args = SCENARIOS[scenario]
        return {"content": None, "tool": (name, args, cid)}
    if "final_answer" in names:
        return {"content": None, "tool": ("final_answer", json.dumps({"answer": ANSWER}), cid)}
    return {"content": ANSWER, "tool": None}


def chat_payload(d: dict, model: str) -> dict:
    msg: dict = {"role": "assistant", "content": d["content"]}
    finish = "stop"
    if d["tool"]:
        name, args, cid = d["tool"]
        msg["tool_calls"] = [{"id": cid, "type": "function", "function": {"name": name, "arguments": args}}]
        finish = "tool_calls"
    return {"id": "chatcmpl-mock", "object": "chat.completion", "created": 1760000000, "model": model,
            "choices": [{"index": 0, "message": msg, "finish_reason": finish}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 12, "total_tokens": 62}}


def chat_stream_chunks(d: dict, model: str) -> list[dict]:
    base = {"id": "chatcmpl-mock", "object": "chat.completion.chunk", "created": 1760000000, "model": model}
    chunks = [dict(base, choices=[{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None}])]
    if d["tool"]:
        name, args, cid = d["tool"]
        chunks.append(dict(base, choices=[{"index": 0, "delta": {"tool_calls": [{"index": 0, "id": cid, "type": "function", "function": {"name": name, "arguments": args}}]}, "finish_reason": None}]))
        finish = "tool_calls"
    else:
        chunks.append(dict(base, choices=[{"index": 0, "delta": {"content": d["content"]}, "finish_reason": None}]))
        finish = "stop"
    chunks.append(dict(base, choices=[{"index": 0, "delta": {}, "finish_reason": finish}]))
    chunks.append(dict(base, choices=[], usage={"prompt_tokens": 50, "completion_tokens": 12, "total_tokens": 62}))
    return chunks


class Handler(BaseHTTPRequestHandler):
    log_path = "requests.jsonl"

    def log_message(self, *a):
        pass

    def _send(self, code: int, obj: dict) -> None:
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"ok": True})
        else:
            self._send(200, {"object": "list", "data": [{"id": "mock-model", "object": "model"}]})

    def do_POST(self):
        parts = self.path.split("/")
        # /r/<run_id>/<scenario>/v1/chat/completions
        try:
            run_id, scenario = parts[2], parts[3]
        except IndexError:
            self._send(404, {"error": {"message": "bad path"}})
            return
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}")
        with LOG_LOCK:
            COUNTS[run_id] = COUNTS.get(run_id, 0) + 1
            seq = COUNTS[run_id]
        over = seq > CEILING
        d = None if over else decide(scenario, body, seq)
        with LOG_LOCK, open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"run_id": run_id, "scenario": scenario, "seq": seq, "path": self.path,
                                "over_ceiling": over, "reply": d, "body": body}, sort_keys=True) + "\n")
        if over:
            self._send(400, {"error": {"message": "mock ceiling reached", "type": "invalid_request_error"}})
            return
        model = body.get("model", "mock-model")
        if body.get("stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            for c in chat_stream_chunks(d, model):
                self.wfile.write(b"data: " + json.dumps(c).encode() + b"\n\n")
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
            return
        self._send(200, chat_payload(d, model))


def main() -> None:
    port, log = int(sys.argv[1]), sys.argv[2]
    Handler.log_path = log
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
