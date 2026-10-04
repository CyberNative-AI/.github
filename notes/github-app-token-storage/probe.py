#!/usr/bin/env python3
"""Synthetic, in-memory SQLite length-constraint demonstration; no credentials."""
import sqlite3

print("SQLite", sqlite3.sqlite_version)
with sqlite3.connect(":memory:") as db:
    db.execute("CREATE TABLE declared (value VARCHAR(40) NOT NULL)")
    db.execute("CREATE TABLE enforced (value TEXT NOT NULL CHECK(length(value) <= 40))")
    for size in (40, 520):
        value = "A" * size  # A size surrogate, not a GitHub token.
        db.execute("DELETE FROM declared")
        db.execute("INSERT INTO declared VALUES (?)", (value,))
        stored = db.execute("SELECT value FROM declared").fetchone()[0]
        if stored != value:
            raise RuntimeError("Unexpected VARCHAR round-trip failure")
        print(f"VARCHAR(40): input={size}, stored={len(stored)}, equal={stored == value}")
        try:
            db.execute("INSERT INTO enforced VALUES (?)", (value,))
        except sqlite3.IntegrityError:
            if size <= 40:
                raise
            print(f"CHECK <=40: input={size}, rejected")
        else:
            if size > 40:
                raise RuntimeError("Expected CHECK constraint rejection")
            print(f"CHECK <=40: input={size}, accepted")
print("PASS: declared length and enforced length differ in this SQLite fixture")
