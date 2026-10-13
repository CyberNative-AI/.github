for v in 1.8.1 1.9.4 1.10.1 1.11.0; do python3 /src/probe_era.py /out/probe-mcp-$v.json -- /senv/py/mcp-$v/bin/python /supp/server_mcp1.py; done
