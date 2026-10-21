#!/bin/bash
# Build all flavors + lint t36. Runs in eclipse-temurin:17-jdk with the work directory mounted at /work.
set -euo pipefail
export ANDROID_HOME=/work/sdk ANDROID_SDK_ROOT=/work/sdk GRADLE_USER_HOME=/work/.gradle
cd /work/app
echo "sdk.dir=/work/sdk" > local.properties
/work/tools/gradle-8.14.3/bin/gradle --no-daemon -q assembleT35Debug assembleT36Debug assembleT36optDebug :app:lintT36Debug 2>&1 | tail -20
find app/build/outputs/apk -name '*.apk' | sort | xargs sha256sum | tee /work/out/APK.sha256
for f in app/build/outputs/apk/*/debug/*.apk; do /work/sdk/build-tools/36.0.0/aapt2 dump badging "$f" | grep -E "^package|targetSdk|sdkVersion"; done | tee /work/out/badging.txt
cp app/build/reports/lint-results-t36Debug.xml /work/out/lint-t36.xml 2>/dev/null || ls app/build/reports
