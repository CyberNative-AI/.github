#!/bin/bash
# One emulator: NAME API W H DENSITY KIND(phone|tablet). Writes /work/out/cells-NAME.jsonl
set -uo pipefail
NAME=$1; API=$2; LW=$3; LH=$4; DEN=$5; KIND=$6
S=/work/sdk; export ANDROID_HOME=$S ANDROID_SDK_ROOT=$S ANDROID_AVD_HOME=/work/avd HOME=/work/home
mkdir -p $ANDROID_AVD_HOME $HOME /work/out/shots; A=$ANDROID_AVD_HOME/$NAME.avd; rm -rf $A; mkdir -p $A
printf 'avd.ini.encoding=UTF-8\npath=%s\ntarget=android-%s\n' $A $API > $ANDROID_AVD_HOME/$NAME.ini
cat > $A/config.ini <<E2
AvdId=$NAME
abi.type=x86_64
hw.cpu.arch=x86_64
image.sysdir.1=system-images/android-$API/google_apis/x86_64/
tag.id=google_apis
target=android-$API
hw.ramSize=3072
disk.dataPartition.size=4G
hw.lcd.width=$LW
hw.lcd.height=$LH
hw.lcd.density=$DEN
hw.keyboard=yes
hw.mainKeys=no
hw.sensors.orientation=yes
PlayStore.enabled=false
E2
ADB="timeout -k 5 60 $S/platform-tools/adb"; OUT=/work/out/cells-$NAME.jsonl; : > $OUT; LOG=/work/out/emu-$NAME.log
boot() {
  $S/emulator/emulator -avd $NAME -no-window -no-audio -no-boot-anim -no-snapshot -wipe-data -gpu swiftshader_indirect -accel on -port 5554 > $LOG 2>&1 &
  EPID=$!
  for i in $(seq 1 120); do sleep 5; [ "$($ADB -s emulator-5554 shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ] && return 0; kill -0 $EPID 2>/dev/null || return 1; done; return 1
}
$ADB start-server >/dev/null 2>&1
if ! boot; then kill $EPID 2>/dev/null; sleep 3; echo "retry boot" >> $LOG; boot || { echo '{"invalid":"boot"}' > $OUT; kill $EPID; exit 3; }; fi
sleep 20
D="$ADB -s emulator-5554"
for k in window_animation_scale transition_animation_scale animator_duration_scale; do $D shell settings put global $k 0; done
$D shell settings put system accelerometer_rotation 0
$D shell input keyevent KEYCODE_WAKEUP; $D shell wm dismiss-keyguard 2>/dev/null
echo "release=$($D shell getprop ro.build.version.release | tr -d '\r') sdk=$($D shell getprop ro.build.version.sdk | tr -d '\r') fp=$($D shell getprop ro.build.fingerprint | tr -d '\r') size=$($D shell wm size | tr -d '\r' | tr '\n' ' ') density=$($D shell wm density | tr -d '\r' | tr '\n' ' ')" > /work/out/device-$NAME.txt
for fl in t35 t36 t36prop t36game; do $D install -r /work/app/app/build/outputs/apk/$fl/debug/app-$fl-debug.apk >> $LOG 2>&1; done
rot() { $D shell wm user-rotation lock $1 >/dev/null 2>&1; $D shell settings put system user_rotation $1; sleep 3; }
# cell FLAVOR ARM REP ROT_START ROT_AFTER(-1 = none) SHOT(0/1)
cell() {
  local fl=$1 arm=$2 rep=$3 r0=$4 r1=$5 shot=$6; local P=ai.cybernative.winprobe.$fl
  [ "$($D shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ] || { echo "{\"device\":\"$NAME\",\"invalid\":\"device lost at $fl $arm $rep\"}" >> $OUT; return 1; }
  rot $r0; $D shell am force-stop $P; $D logcat -c
  $D shell am start -W -n $P/ai.cybernative.winprobe.$arm > /dev/null 2>&1; sleep 4
  local s=$($D logcat -d -s WINPROBE:I | grep " R arm=$arm " | tail -1 | sed 's/.*WINPROBE: //' | tr -d '\r')
  [ "$shot" = 1 ] && $D exec-out screencap -p > /work/out/shots/$NAME-$fl-$arm-r$rep.png
  local a=""; if [ "$r1" != "-1" ]; then $D logcat -c; rot $r1; sleep 2; a=$($D logcat -d -s WINPROBE:I | grep " R arm=$arm " | tail -1 | sed 's/.*WINPROBE: //' | tr -d '\r'); fi
  local top=$($D shell dumpsys activity activities | grep -m1 -E "topResumedActivity" | tr -d '\r' | sed 's/^ *//; s/"//g')
  echo "{\"device\":\"$NAME\",\"api\":$API,\"kind\":\"$KIND\",\"flavor\":\"$fl\",\"arm\":\"$arm\",\"rep\":$rep,\"rot_start\":$r0,\"rot_after\":$r1,\"start\":\"$s\",\"after\":\"$a\",\"top\":\"$top\"}" >> $OUT
}
# landscape start rotation: the first of 0,1 under which OU (t35) reports ori=L
RL=-1; for r in 0 1; do cell t35 OU 0 $r -1 0; if tail -1 $OUT | grep -q '"start":"R arm=OU ori=L'; then RL=$r; break; fi; done
RP=$(( RL == 0 ? 1 : 0 )); echo "{\"device\":\"$NAME\",\"landscape_rotation\":$RL}" >> $OUT
if [ $RL = -1 ]; then echo '{"invalid":"no landscape rotation"}' >> $OUT; fi
for rep in 1 2; do
  if [ $KIND = phone ]; then
    for fl in t35 t36; do for arm in E0 E1 E2; do cell $fl $arm $rep $RP -1 $(( rep == 1 )); done; done
    for fl in t35 t36; do for arm in OU O1 O2 R1; do cell $fl $arm $rep $RL $RP 0; done; done
  else
    for fl in t35 t36 t36prop t36game; do for arm in OU O1 O2 R1; do cell $fl $arm $rep $RL $RP $(( rep == 1 )); done; done
  fi
done
$D emu kill >/dev/null 2>&1; sleep 5; kill $EPID 2>/dev/null; wait $EPID 2>/dev/null
chmod -R a+rX /work/out; echo done $NAME
