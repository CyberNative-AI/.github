"""Shared, SDK-free bookkeeping for the mcp-stdio-cross-era Python client adapters (stdlib only).

Parses `-- SERVER_CMD [ARGS...]`, reads MCP_TOOL / MCP_ARGS, keeps the cumulative monotonic
timings and prints the single result JSON line required by CONTRACT.md. Each client adapter
supplies one async `run(rec, cmd, tool, args)` that drives its SDK's default path.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import threading
import time
from typing import Any, Awaitable, Callable

DEADLINE_S = 40.0  # harness guard only (outer harness kills at 45 s); never passed to an SDK


class Recorder:
    def __init__(self, impl: str) -> None:
        self.t0: float | None = None
        self.stage = "connect"
        self.out: dict[str, Any] = {
            "impl": impl,
            "connect_ok": False,
            "list_ok": False,
            "call_ok": False,
            "tools": None,
            "call_text": None,
            "call_is_error": None,
            "negotiated": None,
            "server_info": None,
            "t_connect_ms": None,
            "t_list_ms": None,
            "t_call_ms": None,
            "error_stage": None,
            "error_type": None,
            "error_msg": None,
        }

    def start(self) -> None:
        """Call immediately before the SDK connect call."""
        self.t0 = time.monotonic()

    def ms(self) -> float:
        assert self.t0 is not None
        return round((time.monotonic() - self.t0) * 1000, 1)

    def done(self, stage: str, next_stage: str | None) -> None:
        self.out[f"{stage}_ok"] = True
        self.out[f"t_{stage}_ms"] = self.ms()
        if next_stage:
            self.stage = next_stage

    def fail(self, exc: BaseException) -> None:
        leaf = _leaf(exc)
        self.out["error_stage"] = self.stage
        self.out["error_type"] = type(leaf).__name__
        msg = str(leaf) or repr(leaf)
        code = getattr(getattr(leaf, "error", None), "code", None)
        if code is not None:
            msg = f"[{code}] {msg}"
        self.out["error_msg"] = msg[:500]


def _leaf(exc: BaseException) -> BaseException:
    """First non-group leaf of a (possibly nested) ExceptionGroup."""
    while isinstance(exc, BaseExceptionGroup) and exc.exceptions:
        exc = exc.exceptions[0]
    return exc


def text_of(content: Any) -> str:
    parts = []
    for item in content or []:
        if getattr(item, "type", None) == "text":
            parts.append(item.text)
    return "".join(parts)


def info_of(obj: Any) -> dict[str, Any] | None:
    if obj is None:
        return None
    return {"name": getattr(obj, "name", None), "version": getattr(obj, "version", None)}


def main(impl: str, run: Callable[[Recorder, list[str], str, dict[str, Any]], Awaitable[None]]) -> int:
    argv = sys.argv[1:]
    if not argv or argv[0] != "--" or len(argv) < 2:
        print(f"usage: {sys.argv[0]} -- SERVER_CMD [ARGS...]", file=sys.stderr)
        return 2
    cmd = argv[1:]
    tool = os.environ.get("MCP_TOOL", "echo")
    args = json.loads(os.environ.get("MCP_ARGS", '{"message":"hello-re13340"}'))
    rec = Recorder(impl)
    lock = threading.Lock()
    emitted = []

    def emit() -> None:
        with lock:
            if emitted:
                return
            emitted.append(True)
            sys.stdout.write(json.dumps(rec.out) + "\n")
            sys.stdout.flush()

    def on_deadline() -> None:
        # Watchdog thread: SDK teardown after a hang can itself take many seconds, so the
        # result line is written at the deadline and the process exits without waiting.
        with lock:
            if not emitted and rec.out["error_stage"] is None:
                rec.fail(TimeoutError(f"harness deadline {DEADLINE_S}s"))
                rec.out["error_type"] = "HarnessDeadline"
        emit()
        os._exit(0)

    watchdog = threading.Timer(DEADLINE_S, on_deadline)
    watchdog.daemon = True
    watchdog.start()

    async def guarded() -> None:
        try:
            await run(rec, cmd, tool, args)
        except BaseException as e:  # noqa: BLE001 - outcome goes into the JSON line
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            if rec.out["error_stage"] is None:
                rec.fail(e)

    try:
        asyncio.run(guarded())
    except BaseException as e:  # noqa: BLE001 - e.g. teardown errors raised after run()
        if isinstance(e, KeyboardInterrupt):
            raise
        if rec.out["error_stage"] is None:
            rec.stage = "close"
            rec.fail(e)
    watchdog.cancel()
    emit()
    return 0
