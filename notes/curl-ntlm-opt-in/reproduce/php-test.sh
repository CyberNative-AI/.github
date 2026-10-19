#!/bin/sh
# X2 exploratory: PHP ext-curl NTLM bit + a CURLAUTH_NTLM proxy request through a local fake-NTLM squid.
set -u
if command -v apk >/dev/null; then apk add --no-cache -q squid >/dev/null 2>&1; else export DEBIAN_FRONTEND=noninteractive; apt-get update -qq >/dev/null; apt-get install -y -qq squid >/dev/null 2>&1; fi
grep PRETTY /etc/os-release | sed 's/^/TAG os /'
php -r '$v=curl_version(); echo "TAG php ".PHP_VERSION." libcurl ".$v["version"]." NTLM_bit=".(($v["features"] & CURL_VERSION_NTLM)?1:0)."\n";'
H=$(find / -name ntlm_fake_auth -type f 2>/dev/null | head -1); echo "TAG helper $H"
mkdir -p /tmp/www && echo OK-TARGET > /tmp/www/index.html
(php -S 127.0.0.1:8000 -t /tmp/www >/dev/null 2>&1 &)
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
sleep 4
cat > /tmp/t.php <<'PH'
<?php
foreach (["NTLM" => CURLAUTH_NTLM, "ANY" => CURLAUTH_ANY] as $name => $auth) {
  $c = curl_init("http://127.0.0.1:8000/");
  curl_setopt($c, CURLOPT_RETURNTRANSFER, true);
  curl_setopt($c, CURLOPT_PROXY, "http://127.0.0.1:3128");
  $set = curl_setopt($c, CURLOPT_PROXYAUTH, $auth);
  curl_setopt($c, CURLOPT_PROXYUSERPWD, "u:p");
  $body = curl_exec($c);
  echo "TAG php-$name setopt=" . var_export($set, true) . " errno=" . curl_errno($c) . " http=" . curl_getinfo($c, CURLINFO_HTTP_CODE) . " body=" . substr((string)$body, 0, 9) . " err=" . curl_error($c) . "\n";
}
PH
php /tmp/t.php 2>&1 | sed 's/^PHP /TAG phpmsg /'
