#!/bin/sh
# Run inside adguard/adguardhome:v0.107.79 with --cap-add NET_ADMIN (see README.md).
# 1. Runs the install wizard and prints the DNS settings it writes.
# 2. For five configs and three Quad9 states (reachable, packets dropped, connections refused):
#    cold: starts AdGuard Home in that state and asks for 10 names;
#    warm: starts it with Quad9 reachable, asks for 5 names, then cuts Quad9 off and asks
#    for the same 5 (cached) and 5 new names.
set -u
apk add -q --no-cache iptables bind-tools curl >/dev/null || { echo "apk add failed"; exit 1; }
AGH=/opt/adguardhome/AdGuardHome
D=/tmp/agh

start() { mkdir -p $D/work; $AGH -c $D/conf/AdGuardHome.yaml -w $D/work --no-check-update >$D/log 2>&1 & PID=$!; }
stop() { kill $PID 2>/dev/null; wait $PID 2>/dev/null; }

echo "== wizard"
mkdir -p $D/conf; start
i=0; until curl -s -o /dev/null http://127.0.0.1:3000/; do i=$((i+1)); [ $i -gt 30 ] && break; sleep 1; done
curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"web":{"ip":"0.0.0.0","port":8080},"dns":{"ip":"0.0.0.0","port":53},"username":"admin","password":"repro-only-password"}' \
  http://127.0.0.1:3000/control/install/configure; echo
sleep 3; stop
cp $D/conf/AdGuardHome.yaml $D/default.yaml
sed -n '/^  upstream_dns:/,/^  fallback_dns:/p' $D/default.yaml

UP='    - https://dns10.quad9.net/dns-query'
conf() {  # $1 = config name
  case $1 in
    default) cp $D/default.yaml $D/conf/AdGuardHome.yaml ;;
    hostname-upstream) sed "s#^$UP\$#    - https://cloudflare-dns.com/dns-query#" $D/default.yaml > $D/conf/AdGuardHome.yaml ;;
    hostname-upstream+bootstrap) sed "s#^$UP\$#    - https://cloudflare-dns.com/dns-query#" $D/default.yaml |
        awk '/^  bootstrap_dns:$/ {print; print "    - 1.1.1.1"; print "    - 1.0.0.1"; skip=1; next}
             skip && /^    - / {next} {skip=0; print}' > $D/conf/AdGuardHome.yaml ;;
    ip-upstream) sed "s#^$UP\$#    - https://1.1.1.1/dns-query#" $D/default.yaml > $D/conf/AdGuardHome.yaml ;;
    fallback) sed 's#^  fallback_dns: \[\]$#  fallback_dns:\n    - 1.1.1.1#' $D/default.yaml > $D/conf/AdGuardHome.yaml ;;
  esac
}
quad9() {  # $1 = mode
  iptables -F OUTPUT
  for net in 9.9.9.0/24 149.112.112.0/24; do
    case $1 in
      drop) iptables -A OUTPUT -d $net -j DROP ;;
      reject) iptables -A OUTPUT -p tcp -d $net -j REJECT --reject-with tcp-reset
              iptables -A OUTPUT -d $net -j REJECT --reject-with icmp-port-unreachable ;;
    esac
  done
}

ask() {  # $1 = label, rest = names; prints resolved count and statuses
  label=$1; shift; ok=0; st=""; n=0
  for name in "$@"; do
    s=$(dig +time=5 +tries=1 @127.0.0.1 $name A | sed -n 's/.*status: \([A-Z]*\).*/\1/p'); s=${s:-TIMEOUT}
    [ "$s" = NOERROR ] && ok=$((ok+1)); st="$st $s"; n=$((n+1))
  done
  echo "  $label resolved=$ok/$n:$(echo $st | tr ' ' '\n' | sort | uniq -c | tr -s ' ' | tr '\n' ',')"
}
ready() { i=0; until curl -s -o /dev/null http://127.0.0.1:8080/; do i=$((i+1)); [ $i -gt 30 ] && break; sleep 1; done; sleep 1; }
FIRST5="example.com wikipedia.org github.com debian.org python.org"
NEXT5="mozilla.org gnu.org kernel.org apache.org nginx.org"

for c in default hostname-upstream hostname-upstream+bootstrap ip-upstream fallback; do
  conf $c
  echo "== $c:$(sed -n '/^  upstream_dns:/,/^  upstream_mode:/p' $D/conf/AdGuardHome.yaml | grep -v 'upstream_dns_file\|upstream_mode' | tr -s ' ' | tr '\n' ' ')"
  for m in reachable drop reject; do
    echo " quad9=$m"
    quad9 $m; rm -rf $D/work; start; ready
    ask "cold" $FIRST5 $NEXT5
    stop
    [ $m = reachable ] && continue
    quad9 reachable; rm -rf $D/work; start; ready
    ask "warm, before" $FIRST5 >/dev/null
    quad9 $m
    ask "warm, cached" $FIRST5
    ask "warm, new" $NEXT5
    stop
  done
done
iptables -F OUTPUT
