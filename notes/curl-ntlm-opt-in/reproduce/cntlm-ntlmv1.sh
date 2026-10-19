#!/bin/sh
# Arm M + control C- inside debian:trixie. Prints tagged lines; raw evidence = full stdout.
set -u
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq >/dev/null
apt-get install -y -qq curl squid cntlm python3 >/dev/null 2>&1
echo "TAG pkg $(dpkg-query -W -f='${Package}=${Version} ' curl squid cntlm)"
cd /tmp
echo TAG posthoc-no-build
echo "TAG C+ $(curl -V | grep -E '^(curl|Features)' | tr '\n' ' ')"
# target + NTLM-only proxy
mkdir -p /srv/www && echo OK-TARGET > /srv/www/index.html
(cd /srv/www && python3 -m http.server 8000 --bind 127.0.0.1 >/dev/null 2>&1 &)
H=$(ls /usr/lib/squid/ntlm_fake_auth 2>/dev/null || find / -name ntlm_fake_auth 2>/dev/null | head -1)
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
cat > /tmp/cntlm.conf <<CN
Username u
Domain D
Password p
Proxy 127.0.0.1:3128
Listen 127.0.0.1:3129
Auth NTLM
CN
sleep 4
cntlm -c /tmp/cntlm.conf -f >/tmp/cntlm.out 2>&1 &
sleep 2
T=http://127.0.0.1:8000/
run() { label=$1; shift; out=$("$@" -s -S -o /tmp/body -w '%{http_code}' $T 2>/tmp/err); rc=$?; echo "TAG M-$label rc=$rc http=$out body=$(head -c 20 /tmp/body 2>/dev/null) err=$(tr '\n' ' ' </tmp/err | cut -c1-160)"; rm -f /tmp/body; }
D="env LD_LIBRARY_PATH=/opt/c-default/lib /opt/c-default/bin/curl"
N="env LD_LIBRARY_PATH=/opt/c-ntlm/lib /opt/c-ntlm/bin/curl"
run p0-plain-direct-no-auth curl -x http://127.0.0.1:3128
run p1-plain-via-cntlm-ntlmv1 curl -x http://127.0.0.1:3129
echo "TAG squid-access $(grep -c . /tmp/access.log 2>/dev/null) lines"; tail -n 12 /tmp/access.log | sed 's/^/TAG access /'
tail -n 5 /tmp/cntlm.out | sed 's/^/TAG cntlm /'
