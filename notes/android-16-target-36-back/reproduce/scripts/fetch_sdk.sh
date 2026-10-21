#!/bin/bash
# Direct download of pinned Android SDK archives (dl.google.com) into $1; logs sha256.
set -euo pipefail
S=$1; mkdir -p $S/dl; cd $S/dl
R=https://dl.google.com/android/repository
get(){ [ -s "$2" ] || curl -fsSL --retry 3 -o "$2" "$1"; }
get $R/platform-tools_r37.0.1-linux.zip pt.zip
get $R/emulator-linux_x64-16428233.zip emu.zip
get $R/platform-36_r02.zip p36.zip
get $R/platform-35_r02.zip p35.zip
get $R/build-tools_r36_linux.zip bt.zip
get $R/sys-img/google_apis/x86_64-36_r07.zip si36.zip
get $R/sys-img/google_apis/x86_64-35_r09.zip si35.zip
sha256sum *.zip > ../ARCHIVES.sha256
cd $S
x(){ d=$2; rm -rf "$d.tmp"; mkdir -p "$d.tmp"; unzip -q "dl/$1" -d "$d.tmp"; mkdir -p "$(dirname $d)"; rm -rf "$d"; mv "$d.tmp"/* "$d"; rmdir "$d.tmp"; }
x pt.zip platform-tools; x emu.zip emulator; x p36.zip platforms/android-36; x p35.zip platforms/android-35
x bt.zip build-tools/36.0.0; x si36.zip system-images/android-36/google_apis/x86_64; x si35.zip system-images/android-35/google_apis/x86_64
ls platforms build-tools system-images/*/google_apis
