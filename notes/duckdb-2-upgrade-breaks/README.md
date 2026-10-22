# DuckDB 2.0.0: what breaks that the migration guides don't say (October 22)

DuckDB 2.0.0 went to PyPI on October 21 at 12:50 UTC. It requires Python 3.11 or newer, so on
those Pythons `pip install -U duckdb` now installs it. DuckDB's
[migration guide](https://duckdb.org/docs/2.0/operations_manual/migration) and
[Python migration guide](https://duckdb.org/docs/2.0/clients/python/migration) list the
breaking changes. On October 22 we ran these changes against DuckDB 1.4.5, 1.5.6 and 2.0.0 and
read the latest releases of the PyPI packages that use DuckDB. The guides leave out three things:

1. **Five libraries still break in their latest release.** dlt, ibis, narwhals,
   sqlglot and marimo each break somewhere on their DuckDB path with 2.0.0. In marimo nothing
   raises: the lookups return `None`.
2. **Your own Python code gets no warning first.** `rel.fetchone()`, `rel.fetchmany()` and
   `rel.execute()` raise `AttributeError` on 2.0.0, and 1.4.5 and 1.5.6 printed no deprecation
   warning for them. The obvious fix, `con.execute(q).fetchone()`, can make the next
   `con.sql(...)` on that connection fail.
3. **The guide's EXPORT/IMPORT route fails on arrow lambdas, and its quick fix doesn't last.**
   If a view or macro uses `x -> x + 1`, `IMPORT DATABASE` on 2.0.0 stops with an error and
   leaves no tables. Setting `lambda_syntax` gets the import through, but the new file then fails
   in every session that doesn't set it.

Until the libraries you use have released fixes, pin `duckdb<2`. DuckDB supports 1.5 until
March 2027; 1.4 LTS ends on November 17, 2026.

## Libraries that break in their latest release

Of the 72 packages among PyPI's 15,000 most downloaded that declare a dependency on `duckdb`,
26 already cap it below 2.0. Six of the rest (five projects: marimo ships as `marimo` and
`marimo-base`) use a removed method, or in sqlglot's case the arrow lambda syntax, outside their
tests in their latest release:

| Package (latest release) | What breaks with duckdb 2.0.0 | Upstream on October 22 |
|---|---|---|
| dlt 1.31.0 | DuckLake destination: the load fails when it closes the connection (`.sql(...).fetchone()`) | [dlt#4595](https://github.com/dlt-hub/dlt/issues/4595) open, no fix yet |
| ibis-framework 12.0.0 | `con.list_tables()` on the DuckDB backend (`execute(...).fetch_arrow_table()`) | changed on main; no release since February 7; [ibis#12196](https://github.com/ibis-project/ibis/issues/12196) open for Arrow batches |
| narwhals 2.27.1 | DuckDB relations with time-zone-aware columns: reading the session time zone (`rel.query(...).fetchone()`) | fixed on main October 16 ([narwhals#4078](https://github.com/narwhals-dev/narwhals/pull/4078)), not released |
| sqlglot 30.24.0 | DuckDB SQL it writes with lambdas: it prints `x -> ...` unless the input used `lambda`, and 2.0.0 rejects that | fixed on main October 21 ([sqlglot#8717](https://github.com/tobymao/sqlglot/pull/8717)), not released |
| marimo 0.25.2 | data sources: default database and schema come back as `None`, and `get_schemas(database=None)` returns an empty list. Nothing raises | no issue found |

We ran the marimo case: with duckdb 1.5.6, marimo 0.25.2 reports `memory` and `main`; with 2.0.0,
`None` and `None`. The other rows come from reading each package's source, and each matches the
upstream issue or fix linked. A package's download count is not its exposure: most narwhals and
sqlglot installs never touch DuckDB. You are affected if you use that package's DuckDB path with
duckdb 2.0.0.

## Removed Python methods, and the fix that fails next

| Call | 1.4.5 | 1.5.6 | 2.0.0 |
|---|---|---|---|
| `duckdb.sql(q).fetchone()`, `duckdb.query(q).fetchone()` | works, no warning | works, no warning | `AttributeError` |
| `con.sql(q).fetchmany(n)` | works, no warning | works, no warning | `AttributeError` |
| `rel.execute()` | works, no warning | works, no warning | `AttributeError` |
| `con.execute(q).arrow()` | works, no warning | works, no warning | `AttributeError` |
| `con.execute(q).fetch_arrow_table()` | works, no warning | `DeprecationWarning` | `AttributeError` |

We recorded warnings with `warnings.simplefilter("always")`, so a warning that Python hides by
default would still have shown up.

2.0.0's error message suggests `rel.limit(1).fetchall()`. The shorter-looking switch to
`con.execute(q).fetchone()` works by itself but leaves the result open, and in 2.0.0 the next
`con.sql(...)` on that connection then fails:

```text
ResourceInUseException: Resource In Use Error: connection has an unfinished result from
execute(); call complete() or abort(), or fetch until a fetch returns no rows, before other
work on this connection, or use a separate connection from cursor()
```

The Python guide documents this change, but the two changes meet in the same line of code. These
forms worked on 1.4.5, 1.5.6 and 2.0.0, including when another `con.sql(...)` followed:

```python
rows = con.sql(q).limit(1).fetchall()   # was con.sql(q).fetchone()
row = rows[0] if rows else None
rows = con.sql(q).limit(n).fetchall()   # was con.sql(q).fetchmany(n)
table = con.sql(q).to_arrow_table()     # was con.execute(q).fetch_arrow_table() or .arrow()
```

`con.complete()` also closes the open result on 2.0.0, but it does not exist on 1.5.6.

To find one-line calls in your code (GNU grep):

```sh
grep -rnE -e '\.(sql|query)\(.*\)\.(fetchone|fetchmany|execute)\(' --include='*.py' .
grep -rnE -e '\.execute\(.*\)\.(fetch_arrow_table|fetch_record_batch|arrow|pl)\(' --include='*.py' .
```

They miss calls split across lines or made on a relation stored in a variable. Each removed call
raises on 2.0.0, so running your tests against 2.0.0 finds the rest.

## EXPORT/IMPORT and arrow lambdas

The migration guide converts a database file with `EXPORT DATABASE` on the old version and
`IMPORT DATABASE` on 2.0.0. We exported a 1.5.6 database with one table, one view and one macro,
each lambda written as `x -> ...`, and imported it on 2.0.0:

| Route on 2.0.0 | Import | New file, new session without the flag |
|---|---|---|
| `IMPORT DATABASE` | fails: `Binder Error: Deprecated lambda arrow (->) detected`; 0 tables | — |
| `SET lambda_syntax = 'enable_single_arrow';` then `IMPORT DATABASE` | works | the view fails with the same error |
| rewrite `schema.sql` to `lambda x:` first, then `IMPORT DATABASE` | works | works |
| `ATTACH` the old file read-only, `COPY FROM DATABASE old TO new` | works | works |
| open the 1.5.6 file directly | works | — |

The same export written with `lambda x: ...` imported without trouble. `EXPORT DATABASE` keeps
the syntax you wrote, so only arrow lambdas fail. The flag is a session setting, which is why the
imported file still needs it later; DuckDB says 2.1 will remove the flag and the arrow syntax.
In `schema.sql`, 1.5.6 wrote each lambda as `(x -> (x + 1))`, so for one-parameter lambdas the
rewrite is `(x -> ` to `(lambda x: `. Lambdas with two parameters, such as `(a, b) -> a + b`, need
the same change by hand.

Opening the old file directly worked for files written at 1.5.6's default storage version. Files
written with `STORAGE_VERSION 'v1.3.0'` or later fail on 2.0.0 for views and macros with arrow
lambdas; DuckDB's open pull request [#27122](https://github.com/duckdb/duckdb/pull/27122)
describes and fixes this.

To find arrow lambdas in SQL files:

```sh
grep -rnE -e "[A-Za-z0-9_)][[:space:]]*->[[:space:]]*[^>'\"[:space:]]" --include='*.sql' .
```

It also lists JSON access by number, such as `j->0`. Don't use it on Python files: type hints
like `) -> str` match too.

## What did not break

DuckDB 2.0.0 also replaced its SQL parser. We split 1,136 public `.sql` files from GitHub code
search into 5,710 statements with 1.5.5 and parsed each with 2.0.0. 2.0.0 parsed 5,707 of them.
The other three were cut short by our tool, not by the parser: 1.5.5's statement splitter rewrites
`PIVOT` and returned a truncated slice. The three whole files parse on 2.0.0, so we found no
statement that 1.5.5 accepted and 2.0.0 rejects. The search returns best matches first, so this is
not a random sample.

## How we tested

- **Python methods and fixes:** [`reproduce/api_check.py`](reproduce/api_check.py) on duckdb
  1.4.5, 1.5.6 and 2.0.0 from PyPI with pyarrow 26.0.0, Python 3.12, one container per version
  without network access, October 22. Output: `reproduce/api-check-*.json`.
- **EXPORT/IMPORT:** [`reproduce/import_trap.py`](reproduce/import_trap.py), `make` with 1.5.6
  and `read` with 2.0.0 in one container. Output: `reproduce/import-trap-1.5.6-to-2.0.0.jsonl`.
  An earlier run of the same cases from 1.4.5 and 1.5.5 to 2.0.0 gave the same import results.
- **marimo:** [`reproduce/marimo_probe.py`](reproduce/marimo_probe.py) with marimo 0.25.2 and
  duckdb 1.5.6 or 2.0.0. Output: `reproduce/marimo-duckdb-*.json`.
- **Package list:** PyPI's 15,000 most downloaded packages (as listed on October 22), filtered to
  those whose latest release declares `duckdb`; we parsed every `.py` file in the latest release
  of each and looked for the removed calls, then read each hit in the source.
- **Commands:** [`reproduce/README.md`](reproduce/README.md).
- We ran this once, ourselves. Nobody has reproduced it independently.

## Limits

- The package scan finds direct calls only, so it can miss some; the counts are a lower bound.
  It covers the latest release of each package, not older versions you may have pinned.
- We ran dlt, ibis, narwhals and sqlglot only as far as reading their source; their own issues
  and fixes confirm each break.
- One day's reading. DuckDB 2.0.x patch releases and new library releases will change the table.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai. We will publish dated corrections here.
