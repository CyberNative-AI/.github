. /lists.sh
case $1 in
 go) python3 /src/run_matrix.py /cfg/CONFIG.json /out --clients $GO --servers $REAL --tag main;;
 py) python3 /src/run_matrix.py /cfg/CONFIG.json /out --clients $PY --servers $REAL --tag main;;
 ts) python3 /src/run_matrix.py /cfg/CONFIG.json /out --clients $TS --servers $REAL --tag main;;
 aux) python3 /src/run_matrix.py /cfg/CONFIG.json /out --servers $FAKE --tag descriptive
      for c in go-sdk-1.8.0 py-mcp-2.3.0 ts-v2-2.3.1; do python3 /src/run_matrix.py /cfg/CONFIG.json /out --clients $c --servers $c --tag notap --notap; done;;
esac
