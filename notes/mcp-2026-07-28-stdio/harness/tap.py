"""Transparent stdio recorder between an MCP client and the server process it launches.

usage: python3 tap.py LOG.jsonl -- SERVER_CMD [ARGS...]

The client is configured to launch this script as its "server". The script starts the real
server, copies bytes in both directions unchanged, and writes one JSON record per complete line
(direction c2s/s2c/err, monotonic ms since start, raw line text) plus a final exit record
(server return code, who closed first). Stdlib only; never alters traffic.
"""

import json
import os
import subprocess
import sys
import threading
import time


def main() -> int:
    log_path = sys.argv[1]
    assert sys.argv[2] == "--"
    cmd = sys.argv[3:]
    t0 = time.monotonic()
    lock = threading.Lock()
    log = open(log_path, "a", encoding="utf-8")

    def rec(kind: str, data: str) -> None:
        with lock:
            log.write(json.dumps({"t_ms": round((time.monotonic() - t0) * 1000, 1), "dir": kind, "line": data}) + "\n")
            log.flush()

    rec("start", json.dumps(cmd))
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
    state = {"client_eof_ms": None}

    def pump(src, dst, kind: str) -> None:
        buf = b""
        while True:
            chunk = os.read(src.fileno(), 65536)
            if not chunk:
                break
            try:
                dst.write(chunk)
                dst.flush()
            except (BrokenPipeError, ValueError, OSError):
                pass
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                rec(kind, line.decode("utf-8", "replace"))
        if buf:
            rec(kind + "-partial", buf.decode("utf-8", "replace"))

    def c2s() -> None:
        pump(sys.stdin.buffer, proc.stdin, "c2s")
        state["client_eof_ms"] = round((time.monotonic() - t0) * 1000, 1)
        rec("client-eof", "")
        try:
            proc.stdin.close()
        except OSError:
            pass

    threading.Thread(target=c2s, daemon=True).start()
    t_out = threading.Thread(target=pump, args=(proc.stdout, sys.stdout.buffer, "s2c"), daemon=True)
    t_err = threading.Thread(target=pump, args=(proc.stderr, sys.stderr.buffer, "err"), daemon=True)
    t_out.start()
    t_err.start()
    rc = proc.wait()
    t_out.join(2)
    t_err.join(2)
    rec("exit", json.dumps({"rc": rc, "client_eof_ms": state["client_eof_ms"]}))
    log.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())
