set -e
bash /src/setup_py.sh
mv /envs/py/mcp-1.12.4 /envs/py-broken-mcp-1.12.4
mv /envs/py/fastmcp-2.14.0 /envs/py-broken-fastmcp-2.14.0
bash /src/setup_py_dated.sh
bash /src/setup_node.sh
