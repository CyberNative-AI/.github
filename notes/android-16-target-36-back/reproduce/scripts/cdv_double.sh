#!/bin/bash
# Double-fire check: full marker lines (with tags) per Back press, Cordova f15t36 vs f14t35 on API 36.
set -uo pipefail
S=/work/sdk; export ANDROID_HOME=$S ANDROID_SDK_ROOT=$S ANDROID_AVD_HOME=/work/avd HOME=/work/home
ADB=$S/platform-tools/adb; D="$ADB -s emulator-5554"; OUT=/work/out/cdv-double-API36.txt; : > $OUT
$S/emulator/emulator -avd a36 -no-window -no-audio -no-boot-anim -no-snapshot -wipe-data -gpu swiftshader_indirect -accel on -port 5554 > /work/out/emu-double.log 2>&1 & EPID=$!
$ADB start-server >/dev/null 2>&1
for i in $(seq 1 120); do sleep 5; [ "$($D shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ] && break; done
sleep 15
for apk in f14t35 f15t36; do $D install -r /work/out/cdv-$apk.apk >/dev/null 2>&1; done
for rep in 1 2 3; do for b in f14t35 f15t36; do
  P=ai.cybernative.cdv.$b; $D shell am force-stop $P; $D logcat -c; $D shell monkey -p $P -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
  for i in $(seq 1 30); do sleep 1; $D logcat -d | grep -q "BACKPROBE READY" && break; done
  sleep 1; $D logcat -c; $D shell input keyevent KEYCODE_BACK; sleep 3
  echo "== rep=$rep $b" >> $OUT; $D logcat -d -v brief | grep "BACKPROBE" >> $OUT
done; done
$D emu kill >/dev/null 2>&1; sleep 5; kill $EPID 2>/dev/null; wait $EPID 2>/dev/null; echo done
