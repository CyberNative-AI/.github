"""marimo 0.25.2 DuckDB engine: default database/schema lookups. Run with marimo and duckdb installed -> JSON on stdout."""
import json, sys, warnings
warnings.simplefilter("always")
import duckdb, marimo
from marimo._sql.engines.duckdb import DuckDBEngine
from marimo._sql.get_engines import engine_to_data_source_connection
con = duckdb.connect()
con.execute("CREATE TABLE t AS SELECT 1 AS a")
e = DuckDBEngine(con)
out = {"duckdb": duckdb.__version__, "marimo": marimo.__version__,
       "get_default_database": e.get_default_database(),
       "get_default_schema": e.get_default_schema(),
       "get_schemas(database=None)": [s.name for s in e.get_schemas(database=None, include_tables=True, include_table_details=False)]}
try:
    c = engine_to_data_source_connection("con", e)
    out["data_source.default_database"] = c.default_database
    out["data_source.default_schema"] = c.default_schema
    out["data_source.databases"] = [(d.name, [s.name for s in d.schemas]) for d in c.databases]
except Exception as ex:
    out["data_source_error"] = repr(ex)
try:
    con.sql("SELECT CURRENT_DATABASE()").fetchone()
    out["direct_rel_fetchone"] = "ok"
except Exception as ex:
    out["direct_rel_fetchone"] = repr(ex)
print(json.dumps(out, indent=1))
