set -e
mkdir -p /w/envs/node && cd /w/envs/node && npm init -y >/dev/null
npm install --ignore-scripts --no-audit --no-fund @lowlysre/icd-10-cm@3.1.1 icdwise@0.1.2 @cyanheads/medical-codes-mcp-server@0.4.1 @easysolutions906/mcp-healthcare@1.1.3 @cosyte/terminology@0.1.0
npm ls --all > /w/out/node-ls.txt || true
node --version > /w/out/node-version.txt
