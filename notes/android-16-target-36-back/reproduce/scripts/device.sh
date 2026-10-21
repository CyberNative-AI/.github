#!/bin/bash
# One emulator device: boot, install 3 flavors, run 7 arms x 2 repeats, write /work/out/matrix-API$1.jsonl
set -uo pipefail
API=$1; S=/work/sdk; export ANDROID_HOME=$S ANDROID_SDK_ROOT=$S ANDROID_AVD_HOME=/work/avd HOME=/work/home
mkdir -p $ANDROID_AVD_HOME $HOME; A=$ANDROID_AVD_HOME/a$API.avd; rm -rf $A; mkdir -p $A
cat > $ANDROID_AVD_HOME/a$API.ini <<E2
avd.ini.encoding=UTF-8
path=$A
target=android-$API
E2
cat > $A/config.ini <<E2
AvdId=a$API
abi.type=x86_64
hw.cpu.arch=x86_64
image.sysdir.1=system-images/android-$API/google_apis/x86_64/
tag.id=google_apis
tag.display=Google APIs
target=android-$API
hw.ramSize=2048
disk.dataPartition.size=4G
hw.lcd.width=1080
hw.lcd.height=2400
hw.lcd.density=420
hw.keyboard=yes
hw.mainKeys=no
PlayStore.enabled=false
E2
ADB=$S/platform-tools/adb; OUT=/work/out/matrix-API$API.jsonl; : > $OUT; LOG=/work/out/emu-API$API.log
boot() {
  $S/emulator/emulator -avd a$API -no-window -no-audio -no-boot-anim -no-snapshot -wipe-data -gpu swiftshader_indirect -accel on -port 5554 > $LOG 2>&1 &
  EPID=$!
  for i in $(seq 1 120); do
    sleep 5; [ "$($ADB -s emulator-5554 shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ] && return 0
    kill -0 $EPID 2>/dev/null || return 1
  done; return 1
}
$ADB start-server >/dev/null 2>&1
if ! boot; then kill $EPID 2>/dev/null; sleep 3; echo "retry boot" >> $LOG; boot || { echo '{"invalid":"boot"}' > $OUT; kill $EPID; exit 3; }; fi
sleep 15
D="$ADB -s emulator-5554"
$D shell settings put global window_animation_scale 0; $D shell settings put global transition_animation_scale 0; $D shell settings put global animator_duration_scale 0
{ echo "release=$($D shell getprop ro.build.version.release | tr -d '\r') sdk=$($D shell getprop ro.build.version.sdk | tr -d '\r') fp=$($D shell getprop ro.build.fingerprint | tr -d '\r') nav=$($D shell settings get secure navigation_mode | tr -d '\r')"; } > /work/out/device-API$API.txt
for fl in t35 t36 t36opt; do $D install -r /work/app/app/build/outputs/apk/$fl/debug/app-$fl-debug.apk >> $LOG 2>&1; done
$D shell input keyevent KEYCODE_WAKEUP; $D shell wm dismiss-keyguard 2>/dev/null
for rep in 1 2; do for fl in t35 t36 t36opt; do for arm in NA NK ND NO XA XK XD; do
  P=ai.cybernative.backprobe.$fl
  $D shell am force-stop $P; $D shell am start -W -n $P/ai.cybernative.backprobe.$arm > /dev/null 2>&1; sleep 2
  $D logcat -c; $D shell input keyevent KEYCODE_BACK; sleep 2
  mk=$($D logcat -d -s BACKPROBE:I | grep -c "HANDLED $arm")
  top=$($D shell dumpsys activity activities | grep -m1 -E "topResumedActivity|mResumedActivity" | tr -d '\r' | sed 's/^ *//')
  still=$(echo "$top" | grep -c "$P/ai.cybernative.backprobe.$arm")
  echo "{\"api\":$API,\"rep\":$rep,\"flavor\":\"$fl\",\"arm\":\"$arm\",\"marker\":$mk,\"still_top\":$still,\"top\":\"$(echo $top | sed 's/"/\\"/g')\"}" >> $OUT
done; done; done

# Cordova builds, if present
for apk in /work/out/cdv-f14t35.apk /work/out/cdv-f14t36.apk /work/out/cdv-f15t36.apk; do [ -f $apk ] && $D install -r $apk >> $LOG 2>&1; done
for rep in 1 2; do for b in f14t35 f14t36 f15t36; do
  [ -f /work/out/cdv-$b.apk ] || continue
  P=ai.cybernative.cdv.$b
  $D shell am force-stop $P; $D logcat -c; $D shell monkey -p $P -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1
  ready=0; for i in $(seq 1 30); do sleep 1; $D logcat -d | grep -q "BACKPROBE READY" && { ready=1; break; }; done
  sleep 1; $D logcat -c; $D shell input keyevent KEYCODE_BACK; sleep 2
  mk=$($D logcat -d | grep -c "BACKPROBE HANDLED CDV")
  top=$($D shell dumpsys activity activities | grep -m1 -E "topResumedActivity|mResumedActivity" | tr -d '\r' | sed 's/^ *//')
  still=$(echo "$top" | grep -c "$P/")
  echo "{\"api\":$API,\"rep\":$rep,\"flavor\":\"$b\",\"arm\":\"CDV\",\"ready\":$ready,\"marker\":$mk,\"still_top\":$still}" >> $OUT
done; done
$D emu kill >/dev/null 2>&1; sleep 5; kill $EPID 2>/dev/null; wait $EPID 2>/dev/null
echo done
