# PyPI download counts: source and query

Source: the public PyPI download dataset in ClickHouse's demo service, table
`pypi.pypi_downloads_per_day_by_version` (one row per project, version and day). It is derived from the public
PyPI download logs on BigQuery. Endpoint: `https://sql-clickhouse.clickhouse.com/?user=demo` (read-only, no key).

The two TSV files in this directory are the output of these queries, first run on 2026-10-13 and run again the
same day (09:08 UTC) with byte-identical output after sorting:

```sql
SELECT version, sum(count) AS c
FROM pypi.pypi_downloads_per_day_by_version
WHERE project = 'mcp' AND date >= '2026-09-12' AND date <= '2026-10-11'
GROUP BY version ORDER BY c DESC
FORMAT TabSeparated
```

The `fastmcp` file uses the same query with `project = 'fastmcp'`.

Date bounds, checked with `min(date)`, `max(date)` and `count(DISTINCT date)` over the same filter: 2026-09-12 to
2026-10-11, 30 days, for both projects. Totals: `mcp` 240,463,855; `fastmcp` 54,628,823.

Share of `mcp` downloads for versions below 1.9 (0.x included):

```sh
awk -F'\t' '{split($1,v,"."); t+=$2; if (v[1]+0<1 || (v[1]==1 && v[2]+0<9)) o+=$2} END {printf "%d / %d = %.2f %%\n", o, t, 100*o/t}' pypi-mcp-versions-20260912-20261011.tsv
```

Downloads include CI jobs, mirrors and client installs. They do not count installed or running servers.
