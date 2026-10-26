#!/bin/bash
# Runs inside node:24.22.1 with /work = a scratch directory holding src/ and fixtures/ (from make_sites.py). Network on (installs only).
set -u
export HOME=/work/home npm_config_cache=/work/home/.npm npm_config_update_notifier=false PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
mkdir -p $HOME /work/sites /work/logs
F=/work/fixtures; S=/work/sites
log(){ echo "[$(date -u +%H:%M:%S)] $*"; }

log docusaurus
( cd $S && rm -rf docusaurus && npx -y create-docusaurus@3.10.2 docusaurus classic --javascript --skip-install --package-manager npm \
  && cp $F/docusaurus/docs/fixture.mdx docusaurus/docs/ && cd docusaurus && npm install --no-audit --no-fund && npm run build \
  && npm ls --depth=0 > /work/logs/docusaurus.versions ) > /work/logs/docusaurus.log 2>&1; log "rc=$?"

log starlight
# Starter pinned to the Starlight 0.42.7 release tag; package.json + package-lock.json are the ones our run resolved
# (@astrojs/starlight 0.42.7, astro 7.4.2), installed with npm ci.
( cd $S && rm -rf starlight && npx -y create-astro@5.3.1 starlight --template 'withastro/starlight/examples/basics#@astrojs/starlight@0.42.7' \
  --no-install --no-git --yes --skip-houston \
  && cp /work/src/starlight/package.json /work/src/starlight/package-lock.json starlight/ \
  && cp $F/starlight/src/content/docs/fixture.mdx starlight/src/content/docs/ && cd starlight && npm ci --no-audit --no-fund && npx astro build \
  && npm ls --depth=0 > /work/logs/starlight.versions ) > /work/logs/starlight.log 2>&1; log "rc=$?"

log vitepress
( rm -rf $S/vitepress && cp -r $F/vitepress $S/vitepress && cd $S/vitepress && npm init -y >/dev/null && npm i --no-audit --no-fund vitepress@1.6.4 \
  && npx vitepress build docs && npm ls --depth=0 > /work/logs/vitepress.versions ) > /work/logs/vitepress.log 2>&1; log "rc=$?"

log mdbook
( rm -rf $S/mdbook && cp -r $F/mdbook $S/mdbook && cd $S/mdbook \
  && curl -fsSL https://github.com/rust-lang/mdBook/releases/download/v0.5.4/mdbook-v0.5.4-x86_64-unknown-linux-gnu.tar.gz | tar xz \
  && ./mdbook --version > /work/logs/mdbook.versions && ./mdbook build ) > /work/logs/mdbook.log 2>&1; log "rc=$?"

log playwright
( mkdir -p /work/pw && cd /work/pw && npm init -y >/dev/null && npm i --no-audit --no-fund playwright@1.62.1 ) > /work/logs/pw.log 2>&1; log "rc=$?"
cp -r $F/g0 $F/g0-prewrap $S/
log done
