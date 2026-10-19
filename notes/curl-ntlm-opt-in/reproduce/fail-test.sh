#!/bin/sh
# Does curl --fail turn the silent --proxy-anyauth 407 into an error? Alpine 3.24 curl (no NTLM), fake-NTLM squid.
set -u
apk add --no-cache -q curl squid python3 >/dev/null 2>&1
grep PRETTY /etc/os-release | sed 's/^/TAG os /'
echo "TAG pkg $(apk info -v 2>/dev/null | grep -E '^(curl|libcurl|squid)-' | tr '\n' ' ')"
echo "TAG curl $(curl -V | grep -E '^(curl|Features)' | tr '\n' ' ')"
H=$(find / -name ntlm_fake_auth -type f 2>/dev/null | head -1); echo "TAG helper $H"
mkdir -p /tmp/www && echo OK-TARGET > /tmp/www/index.html
(cd /tmp/www && python3 -m http.server 8000 --bind 127.0.0.1 >/dev/null 2>&1 &)
cat > /tmp/squid.conf <<SQ
http_port 127.0.0.1:3128
auth_param ntlm program $H
auth_param ntlm children 2
acl authed proxy_auth REQUIRED
http_access allow authed
http_access deny all
cache deny all
pid_filename /tmp/squid.pid
cache_log /tmp/cache.log
access_log stdio:/tmp/access.log
SQ
squid -f /tmp/squid.conf -N >/tmp/squid.out 2>&1 &
sleep 5
T=http://127.0.0.1:8000/
run() { label=$1; shift; out=$("$@" -s -S -o /tmp/body -w '%{http_code}' $T 2>/tmp/err); rc=$?; echo "TAG $label rc=$rc http=$out body=$(head -c 20 /tmp/body 2>/dev/null) err=$(tr '\n' ' ' </tmp/err | cut -c1-160)"; rm -f /tmp/body; }
run anyauth curl -x http://127.0.0.1:3128 --proxy-anyauth -U u:p
run anyauth-fail curl --fail -x http://127.0.0.1:3128 --proxy-anyauth -U u:p
run proxy-ntlm-fail curl --fail -x http://127.0.0.1:3128 --proxy-ntlm -U u:p
run envproxy-fail env http_proxy=http://u:p@127.0.0.1:3128 curl --fail
echo "TAG squid-access $(grep -c . /tmp/access.log 2>/dev/null) lines"; sed 's/^/TAG access /' /tmp/access.log
