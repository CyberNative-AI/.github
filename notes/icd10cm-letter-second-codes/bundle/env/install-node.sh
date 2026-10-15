cd /w/env && mkdir -p node && cd node && npm init -y >/dev/null
for p in @lowlysre/icd-10-cm@3.1.1 icdwise@0.1.2 @cyanheads/medical-codes-mcp-server@0.4.1 @cosyte/terminology@0.1.0 @easysolutions906/mcp-healthcare@1.1.3; do npm install --ignore-scripts --no-audit --no-fund "$p" > "../log-node-$(echo $p|tr '/@' '__').txt" 2>&1 && echo "OK $p" || echo "FAIL $p"; done
npm ls --depth=0 > ../node-ls.txt 2>&1
