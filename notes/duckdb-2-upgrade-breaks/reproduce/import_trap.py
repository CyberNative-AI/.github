"""EXPORT DATABASE on DuckDB 1.x, IMPORT DATABASE on 2.0, with a view and a macro that use an arrow lambda.

python import_trap.py make WORKDIR    (run with DuckDB 1.x)
python import_trap.py read WORKDIR    (run with DuckDB 2.x)   -> JSON lines on stdout
"""
import json
import re
import shutil
import sys

import duckdb

phase, work = sys.argv[1], sys.argv[2]
V = duckdb.__version__


def rec(case, outcome, detail=""):
    print(json.dumps({"duckdb": V, "case": case, "outcome": outcome, "detail": str(detail)}), flush=True)


def err(exc):
    return f"{type(exc).__name__}: {str(exc).splitlines()[0]}"


if phase == "make":
    for kind, lam_filter, lam_add in [("arrow", "x -> x > 1", "x -> x + 1"),
                                      ("python", "lambda x: x > 1", "lambda x: x + 1")]:
        con = duckdb.connect(f"{work}/old_{kind}.db")
        con.execute("CREATE TABLE t AS SELECT [1, 2, 3] AS l")
        con.execute(f"CREATE VIEW v AS SELECT list_filter(l, {lam_filter}) AS r FROM t")
        con.execute(f"CREATE MACRO m(z) AS list_transform(z, {lam_add})")
        con.execute(f"EXPORT DATABASE '{work}/export_{kind}'")
        con.close()
        rec(f"export_{kind}", "OK", open(f"{work}/export_{kind}/schema.sql").read().strip())

elif phase == "read":
    for kind in ["arrow", "python"]:
        for flag in [False, True]:
            con = duckdb.connect()
            if flag:
                con.execute("SET lambda_syntax = 'enable_single_arrow'")
            try:
                con.execute(f"IMPORT DATABASE '{work}/export_{kind}'")
                outcome, detail = "OK", con.execute("SELECT * FROM v").fetchall()
            except Exception as exc:
                outcome, detail = "ERR", err(exc)
            tables = con.execute("SELECT count(*) FROM duckdb_tables()").fetchall()[0][0]
            rec(f"import_{kind}{'_with_flag' if flag else ''}", outcome, f"tables_after={tables} {detail}")
            con.close()
    # the flag is a session setting: import into a file with it, then reopen that file without it
    con = duckdb.connect(f"{work}/imported_with_flag.db")
    con.execute("SET lambda_syntax = 'enable_single_arrow'")
    con.execute(f"IMPORT DATABASE '{work}/export_arrow'")
    con.close()
    con = duckdb.connect(f"{work}/imported_with_flag.db")
    try:
        rec("reopen_imported_file_without_flag", "OK", con.execute("SELECT * FROM v").fetchall())
    except Exception as exc:
        rec("reopen_imported_file_without_flag", "ERR", err(exc))
    con.close()
    con = duckdb.connect()
    con.execute(f"ATTACH '{work}/old_arrow.db' AS old (READ_ONLY)")
    con.execute(f"ATTACH '{work}/new_arrow.db' AS new")
    try:
        con.execute("COPY FROM DATABASE old TO new")
        rec("copy_from_database_arrow", "OK", con.execute("SELECT * FROM new.v").fetchall())
    except Exception as exc:
        rec("copy_from_database_arrow", "ERR", err(exc))
    try:
        rec("open_old_file_directly_arrow", "OK", con.execute("SELECT * FROM old.v").fetchall())
    except Exception as exc:
        rec("open_old_file_directly_arrow", "ERR", err(exc))
    con.close()
    # does the COPY FROM DATABASE result open in a new session without the flag?
    con = duckdb.connect(f"{work}/new_arrow.db")
    try:
        rec("reopen_copied_file_without_flag", "OK", con.execute("SELECT * FROM v").fetchall())
    except Exception as exc:
        rec("reopen_copied_file_without_flag", "ERR", err(exc))
    con.close()
    # rewrite single-parameter arrow lambdas in the export, then import without the flag and reopen
    shutil.copytree(f"{work}/export_arrow", f"{work}/export_rewritten")
    schema = f"{work}/export_rewritten/schema.sql"
    text = open(schema).read()
    open(schema, "w").write(re.sub(r"\(([A-Za-z_][A-Za-z0-9_]*) -> ", r"(lambda \1: ", text))
    rec("rewritten_schema", "OK", open(schema).read().strip())
    con = duckdb.connect(f"{work}/imported_rewritten.db")
    try:
        con.execute(f"IMPORT DATABASE '{work}/export_rewritten'")
        rec("import_rewritten", "OK", con.execute("SELECT * FROM v, (SELECT m([1, 2]))").fetchall())
    except Exception as exc:
        rec("import_rewritten", "ERR", err(exc))
    con.close()
    con = duckdb.connect(f"{work}/imported_rewritten.db")
    try:
        rec("reopen_rewritten_file", "OK", con.execute("SELECT * FROM v, (SELECT m([1, 2]))").fetchall())
    except Exception as exc:
        rec("reopen_rewritten_file", "ERR", err(exc))
    con.close()
