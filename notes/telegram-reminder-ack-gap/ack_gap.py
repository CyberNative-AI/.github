"""Local delivery model: no network, bot account, n8n, or real messages."""
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory


def exercise(crashes=0, consume_first=False, repeated_ack=False):
    with TemporaryDirectory() as directory:
        state = Path(directory) / "state.db"
        sink = Path(directory) / "sink.db"
        with sqlite3.connect(state) as db:
            db.execute("CREATE TABLE reminder (id TEXT PRIMARY KEY, status TEXT)")
            db.execute("INSERT INTO reminder VALUES ('demo', 'pending')")
        with sqlite3.connect(sink) as db:
            db.execute("CREATE TABLE accepted_message (id INTEGER PRIMARY KEY)")
        for attempt in range(crashes + 1):
            with sqlite3.connect(state) as db:
                status = db.execute("SELECT status FROM reminder").fetchone()[0]
            if status == "sent":
                continue
            if consume_first:
                with sqlite3.connect(state) as db:
                    db.execute("UPDATE reminder SET status='sent'")
                break  # failure before the external service accepts anything
            with sqlite3.connect(sink) as db:
                db.execute("INSERT INTO accepted_message DEFAULT VALUES")
            if attempt < crashes:
                continue  # crash after acceptance, before local acknowledgement
            for _ in range(3 if repeated_ack else 1):
                with sqlite3.connect(state) as db:
                    db.execute("UPDATE reminder SET status='sent' WHERE status='pending'")
        with sqlite3.connect(sink) as db:
            accepted = db.execute("SELECT count(*) FROM accepted_message").fetchone()[0]
        with sqlite3.connect(state) as db:
            status = db.execute("SELECT status FROM reminder").fetchone()[0]
        return accepted, status


cases = [
    ("normal", {}, (1, "sent")),
    ("consume_before_send_failure", {"consume_first": True}, (0, "sent")),
    ("one_lost_ack_then_retry", {"crashes": 1}, (2, "sent")),
    ("three_lost_acks_then_retry", {"crashes": 3}, (4, "sent")),
    ("repeated_local_ack_only", {"repeated_ack": True}, (1, "sent")),
]
for name, options, expected in cases:
    observed = exercise(**options)
    if observed != expected:
        raise SystemExit(f"FAIL {name}: {observed!r} != {expected!r}")
    print(f"{name}: accepted={observed[0]}, local_status={observed[1]}")
print("PASS: five local scenarios; external delivery remains untested")
