#!/bin/bash
# OpenSSL 4 on a macOS runner: version gates, -legacy p12 reads, version -e,
# security import, and SKID/AKID on CA-signed leaves. Synthetic fixtures only.
set +e
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$(mktemp -d)"
run() { echo "\$ $*"; ( "$@" ) > out.txt 2>&1; rc=$?; sed 's/^/  /' out.txt | head -20; echo "  [rc=$rc]"; }
echo "## image"
sw_vers; uname -m; echo "ImageOS=$ImageOS ImageVersion=$ImageVersion"
echo "which -a openssl:"; which -a openssl
openssl version
brew list --versions openssl@3 openssl@4 libressl
P=$(brew --prefix)
echo "include/openssl -> $(readlink "$P/include/openssl" 2>&1)"
echo "lib/libssl.dylib -> $(readlink "$P/lib/libssl.dylib" 2>&1)"
echo "pkg-config openssl: $(PKG_CONFIG_PATH=$P/lib/pkgconfig pkg-config --modversion openssl 2>&1)"
brew info --json=v2 openssl@4 2>/dev/null | python3 -c 'import json,sys;f=json.load(sys.stdin)["formulae"][0];print("openssl@4 formula:",f["versions"]["stable"],"keg_only=",f["keg_only"],"installed=",[i["version"] for i in f["installed"]],"linked_keg=",f["linked_keg"])'
if ! brew list --versions openssl@4 >/dev/null; then HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_CLEANUP=1 brew install openssl@4 >/dev/null 2>&1; echo "installed openssl@4: $?"; fi
O3="$(brew --prefix openssl@3)/bin/openssl"; O4="$(brew --prefix openssl@4)/bin/openssl"; LS=/usr/bin/openssl
for o in "$O3" "$O4" "$LS"; do echo "$o: $($o version)"; done

echo; echo "## fixtures (made with openssl@3)"
"$O3" req -x509 -newkey rsa:2048 -nodes -keyout id.key -out id.crt -days 2 -subj "/CN=Test Developer ID" 2>/dev/null
"$O3" pkcs12 -export -legacy -in id.crt -inkey id.key -out legacy.p12 -passout pass:test
"$O3" pkcs12 -in legacy.p12 -info -noout -legacy -passin pass:test 2>&1 | grep -E "PKCS7|Shrouded|MAC"

gate() { # $1 binary dir on PATH, $2 regex
  ( export PATH="$1:$PATH"
    LEGACY_FLAG=""
    if openssl version 2>/dev/null | grep -q "$2"; then LEGACY_FLAG="-legacy"; fi
    echo "  openssl=$(openssl version) gate='$2' LEGACY_FLAG='$LEGACY_FLAG'"
    openssl pkcs12 -in legacy.p12 -out temp_cert.pem -clcerts -nokeys $LEGACY_FLAG -passin pass:test > g.txt 2>&1; r1=$?
    openssl pkcs12 -in legacy.p12 -out temp_key.pem -nocerts -nodes $LEGACY_FLAG -passin pass:test >> g.txt 2>&1; r2=$?
    echo "  cert read rc=$r1, key read rc=$r2"; head -3 g.txt | sed 's/^/    /' )
}
echo; echo "## version-check gate on the same RC2-40 .p12"
for d in "$(dirname "$O3")" "$(dirname "$O4")" /usr/bin; do
  gate "$d" '^OpenSSL 3'
  gate "$d" '^OpenSSL [3-9]'
done
echo; echo "## pkcs12 read without/with -legacy"
for o in "$O3" "$O4"; do run "$o" pkcs12 -in legacy.p12 -nokeys -passin pass:test -out /dev/null; run "$o" pkcs12 -in legacy.p12 -nokeys -legacy -passin pass:test -out /dev/null; done
echo; echo "## openssl version -e / -m"
for o in "$O3" "$O4"; do run "$o" version -e; run "$o" version -m; done
echo "version -e line that sets an environment variable, on 4.x:"; ( export PATH="$(dirname "$O4"):$PATH"; echo "[$(echo $(openssl version -e | sed -n -e 's/engines-.*//' -e 's/: "/=/p'))]" )

echo; echo "## export without -legacy, then security import"
"$O4" pkcs12 -export -in id.crt -inkey id.key -out o4.p12 -passout pass:test
"$O4" pkcs12 -in o4.p12 -info -noout -passin pass:test 2>&1 | grep -E "PKCS7|Shrouded|MAC|PBES2|PBKDF2" | head -6
"$O3" pkcs12 -export -in id.crt -inkey id.key -out o3.p12 -passout pass:test
security create-keychain -p kc probe.keychain-db
security unlock-keychain -p kc probe.keychain-db
for f in legacy.p12 o3.p12 o4.p12; do run security import "$f" -k probe.keychain-db -P test -T /usr/bin/codesign; done
security find-identity -v probe.keychain-db
security delete-keychain probe.keychain-db

echo; echo "## CA-signed leaf with -extfile (SAN only vs SAN+SKID/AKID)"
for o in "$O3" "$O4"; do
  v=$("$o" version | cut -d' ' -f2); mkdir -p "ca-$v"; cd "ca-$v"
  "$o" req -x509 -newkey rsa:2048 -nodes -keyout ca.key -out ca.crt -days 2 -subj "/CN=Probe CA" \
    -addext "basicConstraints=critical,CA:TRUE" -addext "keyUsage=critical,keyCertSign,cRLSign" 2>/dev/null
  "$o" req -newkey rsa:2048 -nodes -keyout srv.key -out srv.csr -subj "/CN=localhost" 2>/dev/null
  printf 'subjectAltName=DNS:localhost\n' > san.cnf
  printf 'subjectAltName=DNS:localhost\nsubjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid,issuer\n' > san-fixed.cnf
  "$o" x509 -req -in srv.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out srv.crt -days 2 -extfile san.cnf 2>/dev/null
  "$o" x509 -req -in srv.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out srv-fixed.crt -days 2 -extfile san-fixed.cnf 2>/dev/null
  for c in srv.crt srv-fixed.crt; do
    echo "  $v $c: $("$o" x509 -in $c -noout -ext subjectKeyIdentifier,authorityKeyIdentifier 2>&1 | grep -c 'Key Identifier') key-identifier extensions"
    python3 "$HERE/tls_check.py" ca.crt "$c" srv.key | sed 's/^/    /'
  done
  cd ..
done
python3 -c 'import ssl,sys;print("python",sys.version.split()[0],ssl.OPENSSL_VERSION)'
