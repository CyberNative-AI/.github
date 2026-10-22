#!/bin/bash
# A typical Apple signing step: read an RC2-40 .p12 with a version check, re-export
# it, import it into a temporary keychain. Run under bash -e with each openssl first
# on PATH, once with '^OpenSSL 3' and once with '^OpenSSL [3-9]'. Synthetic certificate.
set +e
O3="$(brew --prefix openssl@3)/bin/openssl"
brew list --versions openssl@4 >/dev/null || HOMEBREW_NO_AUTO_UPDATE=1 brew install openssl@4 >/dev/null 2>&1
O4="$(brew --prefix openssl@4)/bin/openssl"
sw_vers -productVersion; echo "ImageVersion=$ImageVersion"
STEP='
security create-keychain -p build probe.keychain
security unlock-keychain -p build probe.keychain
LEGACY_FLAG=""
if openssl version 2>/dev/null | grep -q "$GATE"; then
  LEGACY_FLAG="-legacy"
fi
openssl pkcs12 -in certificate.p12 -out cert.pem -clcerts -nokeys $LEGACY_FLAG -passin pass:"$P12_PASSWORD"
openssl pkcs12 -in certificate.p12 -out key.pem -nocerts -nodes $LEGACY_FLAG -passin pass:"$P12_PASSWORD"
openssl pkcs12 -export -out converted.p12 -inkey key.pem -in cert.pem -passout pass:"$P12_PASSWORD" -keypbe PBE-SHA1-3DES -certpbe PBE-SHA1-3DES -macalg sha1
security import converted.p12 -k probe.keychain -P "$P12_PASSWORD" -T /usr/bin/codesign
'
for gate in '^OpenSSL 3' '^OpenSSL [3-9]'; do
for d in "$(dirname "$O3")" "$(dirname "$O4")" /usr/bin; do
  T=$(mktemp -d); cd "$T"
  "$O3" req -x509 -newkey rsa:2048 -nodes -keyout k.pem -out c.pem -days 2 -subj "/CN=Probe Developer ID" \
     -addext "extendedKeyUsage=codeSigning" -addext "keyUsage=critical,digitalSignature" 2>/dev/null
  "$O3" pkcs12 -export -legacy -in c.pem -inkey k.pem -out certificate.p12 -passout pass:probe-pass
  rm k.pem c.pem
  ( export PATH="$d:$PATH" P12_PASSWORD=probe-pass GATE="$gate"
    bash -e -c "$STEP" > log.txt 2>&1; rc=$?
    echo "gate='$gate' | $(openssl version | cut -d' ' -f1-2) | step rc=$rc | identities in keychain: $(security find-identity -p codesigning probe.keychain 2>/dev/null | grep -c 'Probe Developer ID')"
    [ $rc -ne 0 ] && tail -2 log.txt | sed 's/^/    /' )
  security delete-keychain probe.keychain 2>/dev/null
  cd /; rm -rf "$T"
done; done
