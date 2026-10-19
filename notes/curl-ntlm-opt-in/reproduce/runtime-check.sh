#!/usr/bin/env bash
# Install each image's own curl package and print `curl -V`. Writes runtime/<name>.txt.
# The NTLM answer is whether "NTLM" appears on the Features line.
set -u
out=$(dirname "$0")/runtime; mkdir -p "$out"
APT='export DEBIAN_FRONTEND=noninteractive; apt-get update -qq >/dev/null && apt-get install -y -qq curl >/dev/null 2>&1; dpkg-query -W curl libcurl4t64 libcurl4 2>/dev/null; cat /etc/os-release | grep -E "^(PRETTY_NAME|VERSION_CODENAME)"'
APK='apk add --no-cache -q curl >/dev/null; apk info -v 2>/dev/null | grep -E "^(curl|libcurl)-"; cat /etc/os-release | grep PRETTY'
DNF='echo "DEFAULT:"; rpm -q curl curl-minimal libcurl libcurl-minimal; curl -V | head -4; echo "FULL:"; dnf -y -q swap curl-minimal curl --allowerasing >/dev/null 2>&1 || dnf -y -q install curl --allowerasing >/dev/null 2>&1; dnf -y -q swap libcurl-minimal libcurl --allowerasing >/dev/null 2>&1; rpm -q curl curl-minimal libcurl libcurl-minimal; grep PRETTY /etc/os-release'
row() { name=$1; img=$2; cmd=$3
  docker run --rm --cpus 2 --memory 2g --entrypoint sh "$img" -c "$cmd; echo ===; curl -V" > "$out/$name.txt" 2>&1
  echo "$name rc=$? $(grep -m1 '^curl ' "$out/$name.txt" | cut -c1-40) NTLM=$(grep -c '^Features:.*NTLM' "$out/$name.txt")"; }
for spec in "c-plus-debian-trixie|debian:trixie|$APT" "debian-sid|debian:sid|$APT" "debian-testing|debian:testing|$APT" \
  "ubuntu-rolling|ubuntu:rolling|$APT" "ubuntu-devel|ubuntu:devel|$APT" "ubuntu-latest-extra|ubuntu:latest|$APT" \
  "alpine-edge|alpine:edge|$APK" "alpine-latest|alpine:latest|$APK" "wolfi|cgr.dev/chainguard/wolfi-base:latest|$APK" \
  "fedora-rawhide|fedora:rawhide|$DNF" "fedora-latest|fedora:latest|$DNF" \
  "arch|archlinux:latest|pacman -Sy --noconfirm --needed curl >/dev/null 2>&1; pacman -Q curl" \
  "opensuse-tw|opensuse/tumbleweed:latest|zypper -n -q in curl >/dev/null 2>&1; rpm -q curl libcurl4" \
  "curlimages|curlimages/curl:latest|true"; do
  IFS='|' read -r n i c <<<"$spec"; row "$n" "$i" "$c"; done
