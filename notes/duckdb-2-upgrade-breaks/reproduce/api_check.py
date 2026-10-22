"""DuckDB Python API check: removed fetch methods, warnings before removal, replacements, open-result trap.

Run once per DuckDB version: python api_check.py  -> JSON on stdout. Needs duckdb and pyarrow.
Each case uses a fresh in-memory connection unless it says otherwise.
"""
import json
import warnings

import duckdb

CASES = [
    # removed in 2.0: did 1.x warn first?
    ("removed: duckdb.sql(q).fetchone()", ["duckdb.sql('SELECT 1').fetchone()"]),
    ("removed: con.sql(q).fetchmany(1)", ["con.sql('SELECT 1').fetchmany(1)"]),
    ("removed: duckdb.query(q).fetchone()", ["duckdb.query('SELECT 1').fetchone()"]),
    ("removed: rel.execute()", ["con.sql('SELECT 1').execute()"]),
    ("removed: con.execute(q).fetch_arrow_table()", ["con.execute('SELECT 1').fetch_arrow_table()"]),
    ("removed: con.execute(q).arrow()", ["con.execute('SELECT 1').arrow()"]),
    # replacements
    ("works: con.sql(q).limit(1).fetchall()", ["con.sql('SELECT * FROM range(10)').limit(1).fetchall()"]),
    ("works: con.sql(q).limit(2).fetchall()", ["assert len(con.sql('SELECT * FROM range(10)').limit(2).fetchall()) == 2"]),
    ("works: con.sql(q).fetchall()", ["con.sql('SELECT 1').fetchall()"]),
    ("works: con.execute(q).fetchall()", ["con.execute('SELECT 1').fetchall()"]),
    ("works: con.sql(q).to_arrow_table()", ["con.sql('SELECT 1').to_arrow_table()"]),
    ("works: con.execute(q).fetchone()", ["con.execute('SELECT 1').fetchone()"]),
    # the open-result trap after the obvious replacement
    ("trap: execute(q).fetchone() then con.sql(q2).fetchall()",
     ["con.execute('SELECT 1').fetchone()", "con.sql('SELECT 2').fetchall()"]),
    ("trap: execute(range).fetchone() then con.sql(q2).fetchall()",
     ["con.execute('SELECT * FROM range(10)').fetchone()", "con.sql('SELECT 2').fetchall()"]),
    ("trap: duckdb.execute(q).fetchone() then duckdb.sql(q2).fetchall()",
     ["duckdb.execute('SELECT 1').fetchone()", "duckdb.sql('SELECT 2').fetchall()"]),
    ("no trap: execute(q).fetchone() then con.execute(q2).fetchall()",
     ["con.execute('SELECT 1').fetchone()", "con.execute('SELECT 2').fetchall()"]),
    ("no trap: execute(q).fetchall() then con.sql(q2).fetchall()",
     ["con.execute('SELECT 1').fetchall()", "con.sql('SELECT 2').fetchall()"]),
    ("no trap: limit(1).fetchall() then con.sql(q2).fetchall()",
     ["con.sql('SELECT * FROM range(10)').limit(1).fetchall()", "con.sql('SELECT 2').fetchall()"]),
    ("no trap: limit(2).fetchall() then con.sql(q2).fetchall()",
     ["con.sql('SELECT * FROM range(10)').limit(2).fetchall()", "con.sql('SELECT 2').fetchall()"]),
    ("no trap: to_arrow_table() then con.sql(q2).fetchall()",
     ["con.sql('SELECT * FROM range(10)').to_arrow_table()", "con.sql('SELECT 2').fetchall()"]),
]


def run(steps):
    con = duckdb.connect()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            for step in steps:
                exec(step, {"con": con, "duckdb": duckdb})
            outcome = "OK"
        except Exception as exc:  # record the exact error
            outcome = f"{type(exc).__name__}: {str(exc).splitlines()[0]}"
    con.close()
    return {"outcome": outcome, "warnings": [f"{w.category.__name__}: {w.message}" for w in caught]}


print(json.dumps({"duckdb": duckdb.__version__,
                  "cases": {name: run(steps) for name, steps in CASES}}, indent=1))
