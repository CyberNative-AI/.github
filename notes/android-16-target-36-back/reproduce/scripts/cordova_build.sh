#!/bin/bash
set -euo pipefail
export ANDROID_HOME=/work/sdk ANDROID_SDK_ROOT=/work/sdk GRADLE_USER_HOME=/work/.gradle HOME=/work/home
mkdir -p $HOME /work/cdv
cd /work/tools; [ -d node-v22.23.4-linux-x64 ] || { curl -fsSL -o node.tgz https://nodejs.org/dist/v22.23.4/node-v22.23.4-linux-x64.tar.xz; tar xJf node.tgz; }
export PATH=/work/tools/node-v22.23.4-linux-x64/bin:/work/tools/gradle-8.14.3/bin:$PATH
npm config set cache /work/.npm >/dev/null
[ -x /work/tools/cdvcli/node_modules/.bin/cordova ] || { mkdir -p /work/tools/cdvcli; cd /work/tools/cdvcli; npm init -y >/dev/null; npm i -s cordova@13.0.0 >/dev/null; }
CDV=/work/tools/cdvcli/node_modules/.bin/cordova
mk(){ name=$1 ver=$2 t36=$3; cd /work/cdv; rm -rf $name; $CDV create $name ai.cybernative.cdv.$name CdvProbe >/dev/null; cd $name
  cat > www/js/index.js <<'JS'
document.addEventListener('deviceready', function () {
  document.addEventListener('backbutton', function () { console.log('BACKPROBE HANDLED CDV'); }, false);
  console.log('BACKPROBE READY');
}, false);
JS
  if [ "$t36" = 1 ]; then sed -i 's#</widget>#    <preference name="android-targetSdkVersion" value="36" />\n</widget>#' config.xml; fi
  $CDV telemetry off >/dev/null 2>&1 || true
  $CDV platform add android@$ver --nosave >/dev/null
  $CDV build android --debug > /work/out/cdv-$name-build.log 2>&1 || { grep -E "What went wrong|>|error" /work/out/cdv-$name-build.log | head -20; exit 1; }
  apk=$(find platforms/android -name '*debug*.apk' | head -1); cp $apk /work/out/cdv-$name.apk
  /work/sdk/build-tools/36.0.0/aapt2 dump badging /work/out/cdv-$name.apk | grep -E "^package|targetSdk" ; }
mk f14t35 14.0.1 0; mk f14t36 14.0.1 1; mk f15t36 15.1.0 0
sha256sum /work/out/cdv-*.apk | tee /work/out/CDV-APK.sha256
