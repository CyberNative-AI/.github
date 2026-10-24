#!/bin/bash
# Build the 4 flavors, then lint the target-36 one. eclipse-temurin:17-jdk; /work = this folder, /work/sdk = Android SDK, /work/tools = Gradle
set -euo pipefail
export ANDROID_HOME=/work/sdk ANDROID_SDK_ROOT=/work/sdk GRADLE_USER_HOME=/work/.gradle
cd /work/app; echo "sdk.dir=/work/sdk" > local.properties
/work/tools/gradle-8.14.3/bin/gradle --no-daemon -q assembleT35Debug assembleT36Debug assembleT36propDebug assembleT36gameDebug :app:lintT36Debug 2>&1 | tail -30
find app/build/outputs/apk -name '*.apk' | sort | xargs sha256sum | tee /work/out/APK.sha256
for f in app/build/outputs/apk/*/debug/*.apk; do /work/sdk/build-tools/36.0.0/aapt2 dump badging "$f" | grep -E "^package|targetSdk"; /work/sdk/build-tools/36.0.0/aapt2 dump xmltree --file AndroidManifest.xml "$f" | grep -E "appCategory|PROPERTY_COMPAT|screenOrientation|resizeable|maxAspect" ; done > /work/out/badging.txt 2>&1
cp app/build/reports/lint-results-t36Debug.xml /work/out/lint-t36.xml 2>/dev/null || true
cp app/build/reports/lint-results-t36Debug.txt /work/out/lint-t36.txt 2>/dev/null || true
chmod -R a+rX /work/out
