#!/bin/sh
# Install-line probe. env: G (G1..G4), TAG, REP; mount /work (rw)
set -u
O="/work/$TAG"; mkdir -p "$O"; P="$O/$G-r$REP"
rec() { k=$1; shift; out=$("$@" 2>&1); rc=$?; printf '%s\t%s\n' "$k" "$rc" >>"$P.rc"; printf '### %s rc=%s\n%s\n' "$k" "$rc" "$(printf '%s' "$out" | tail -c 3000)" >>"$P.log"; return $rc; }
: >"$P.rc"; : >"$P.log"
printf 'node\t%s\n' "$(node --version)" >>"$P.rc"
printf 'os\t%s\n' "$(. /etc/os-release; echo ${VERSION_CODENAME:-$ID-$VERSION_ID})" >>"$P.rc"
export COREPACK_ENABLE_DOWNLOAD_PROMPT=0
case "$G" in
G1)
  rec cmd_yarn sh -c 'command -v yarn'
  rec cmd_corepack sh -c 'command -v corepack'
  rec cmd_pnpm sh -c 'command -v pnpm'
  rec cmd_apt_key sh -c 'command -v apt-key'
  rec yarn_version yarn --version
  ;;
G2)
  rec npm_g_yarn npm install --global yarn
  rec yarn_version yarn --version
  ;;
G3)
  rec cond_install sh -c 'command -v yarn >/dev/null 2>&1 || npm install --global yarn@1.22.22'
  rec yarn_version yarn --version
  ;;
G4)
  rec npm_g_corepack npm install --global corepack
  rec corepack_version corepack --version
  rec corepack_enable corepack enable
  mkdir -p /tmp/p && cd /tmp/p && printf '{"name":"p","version":"1.0.0","packageManager":"yarn@1.22.22"}\n' >package.json
  rec yarn_version yarn --version
  ;;
esac
echo DONE >>"$P.rc"
