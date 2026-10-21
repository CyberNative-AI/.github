#!/bin/bash
export ANDROID_HOME=/work/sdk ANDROID_SDK_ROOT=/work/sdk GRADLE_USER_HOME=/work/.gradle
cd /work/app-lintdef; echo "sdk.dir=/work/sdk" > local.properties
G=/work/tools/gradle-8.14.3/bin/gradle
$G --no-daemon -q assembleT36Release > /work/out/lintdef-assembleT36Release.log 2>&1; echo "assembleT36Release rc=$?"
ls app/build/outputs/apk/t36/release/ 2>/dev/null
$G --no-daemon -q lintT35Debug > /work/out/lintdef-lintT35.log 2>&1; echo "lintT35Debug rc=$?"
$G --no-daemon -q lintT36Debug > /work/out/lintdef-lintT36.log 2>&1; echo "lintT36Debug(default abortOnError) rc=$?"
cp app/build/reports/lint-results-t35Debug.xml /work/out/lintdef-t35.xml 2>/dev/null; cp app/build/reports/lint-results-t36Debug.xml /work/out/lintdef-t36.xml 2>/dev/null
ls app/build/intermediates/lint_vital* -d 2>/dev/null | head -3
