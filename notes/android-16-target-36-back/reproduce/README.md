# Android 16 target-36 Back handlers: reproduction

These are the test app and scripts we ran on 2026-10-21. One change: the log tag and marker text were renamed to `BACKPROBE`; nothing else differs. The scripts expect this folder mounted at `/work` in a container, with the Android SDK in `sdk/`, Gradle in `tools/gradle-8.14.3/` and output in `out/`. Builds download from Google's Maven repository, Maven Central and (for Cordova) npm and nodejs.org.

Image, pinned by digest: `eclipse-temurin:17-jdk` = `eclipse-temurin@sha256:fe947d993c32dd9cf651a4353a6ed723c2370b3a9d034ea4cab4775404ea531a` (linux/amd64). The emulator needs `/dev/kvm` on an x86_64 Linux host.

```sh
IMG=eclipse-temurin@sha256:fe947d993c32dd9cf651a4353a6ed723c2370b3a9d034ea4cab4775404ea531a
mkdir -p out tools
curl -fsSLo tools/gradle.zip https://services.gradle.org/distributions/gradle-8.14.3-bin.zip && unzip -q tools/gradle.zip -d tools
bash scripts/fetch_sdk.sh "$PWD/sdk"   # pinned SDK archives from dl.google.com (subject to Google's SDK licence), about 3 GB unpacked
```

`fetch_sdk.sh` downloads platform-tools r37.0.1, emulator 16428233, platforms 35 and 36 (r02), build-tools 36.0.0 and the Google APIs x86_64 system images for API 36 (r07) and API 35 (r09), and writes their sha256 to `ARCHIVES.sha256`.

## 1. Build the test app

`app/` builds one app in three flavors from the same source: `t35` (targetSdk 35), `t36` (36) and `t36opt` (36, plus `src/t36opt/AndroidManifest.xml`, which sets `android:enableOnBackInvokedCallback="false"` on `<application>`). Android Gradle Plugin 8.11.1, Gradle 8.14.3, compileSdk 36, AppCompat 1.7.1. Each Activity handles Back one way and, when its handler runs, logs `HANDLED <name>` with the tag `BACKPROBE`:

| Activity | Handler |
|---|---|
| `NA` | `android.app.Activity`, overrides `onBackPressed()` without calling `super` |
| `NK` | `Activity`, `onKeyDown` returns `true` for `KEYCODE_BACK` |
| `ND` | `Activity` that shows an `android.app.Dialog` overriding `onBackPressed()` |
| `NO` | `Activity`, no handler (control: must close) |
| `XA` | `AppCompatActivity`, overrides `onBackPressed()` |
| `XK` | `AppCompatActivity`, `onKeyDown` for `KEYCODE_BACK` |
| `XD` | `AppCompatActivity`, `OnBackPressedDispatcher` callback (control: must be handled) |

```sh
docker run --rm --cpus 6 --memory 6g --memory-swap 6g --pids-limit 4096 -v "$PWD:/work" "$IMG" /work/scripts/build.sh
```

## 2. Press Back on each screen, on Android 16 and Android 15

`device.sh <api>` creates a fresh emulator, installs the three flavors and, for every flavor and Activity, twice: force-stops the app, starts the Activity, waits 2 s, sends `adb shell input keyevent KEYCODE_BACK` and waits 2 s. It writes one line per trial to `out/matrix-API<api>.jsonl`: `marker` counts the `BACKPROBE HANDLED` log lines, `still_top` is 1 if the Activity is still the resumed one. "Handled" in the note means both are 1 (for `ND`, the dialog's marker). If the Cordova APKs from step 4 exist, it tests them the same way.

```sh
for api in 36 35; do
  docker run --rm --cpus 6 --memory 8g --memory-swap 8g --pids-limit 4096 --device /dev/kvm -v "$PWD:/work" "$IMG" bash -c \
    'apt-get -qq update; apt-get -qq install -y libpulse0 libnss3 libxcomposite1 libxcursor1 libxi6 libxtst6 libasound2t64 libgl1 libdrm2 libxkbfile1 libxdamage1 libxrandr2 libxkbcommon0 libbsd0 libgbm1; /work/scripts/device.sh '$api
done
```

Our results: [`results/matrix-API36.jsonl`](results/matrix-API36.jsonl) and [`results/matrix-API35.jsonl`](results/matrix-API35.jsonl); the emulator builds are in `results/device-API*.txt`. Both system images default to gesture navigation (`navigation_mode=2`); the input we tested is the injected Back key either way.

## 3. Lint with stock settings

`app/app/build.gradle` has a `lint { ... }` block that keeps the first build going. For stock behaviour, copy `app/` to `app-lintdef/` and delete that one line, then:

```sh
cp -r app app-lintdef && sed -i '/^  lint {/d' app-lintdef/app/build.gradle
docker run --rm --cpus 6 --memory 6g --memory-swap 6g --pids-limit 4096 -v "$PWD:/work" "$IMG" /work/scripts/lintdef.sh
```

It runs `assembleT36Release` (exit 0 in our run), then `lintT35Debug` and `lintT36Debug`. Both lint tasks exited 1 in our run. At target 35 that is only `MissingSuperCall` (Error) on `XA`, which does not call `super` on purpose. `GestureBackNavigation` appears only at target 36: [`results/lintdef-t36.xml`](results/lintdef-t36.xml) against [`results/lintdef-t35.xml`](results/lintdef-t35.xml).

## 4. Cordova

`cordova_build.sh` installs Node 22.23.4 and Cordova CLI 13.0.0, creates three plugin-free apps with a `backbutton` listener that logs `BACKPROBE HANDLED CDV`, and builds them: `f14t35` (cordova-android 14.0.1, default target 35), `f14t36` (14.0.1 plus `<preference name="android-targetSdkVersion" value="36" />`) and `f15t36` (15.1.0, default target 36). Then run step 2 again. `cdv_double.sh` boots the API 36 emulator once more and records the full marker lines for three presses each of `f14t35` and `f15t36`: [`results/cdv-double-API36.txt`](results/cdv-double-API36.txt).

```sh
docker run --rm --cpus 6 --memory 6g --memory-swap 6g --pids-limit 4096 -v "$PWD:/work" "$IMG" bash -c 'apt-get -qq update; apt-get -qq install -y xz-utils; /work/scripts/cordova_build.sh'
```

## 5. Census

Needs Python 3 and `git`; it clones about 750 public repositories (blob-limited) and sends about 760 requests to play.google.com.

```sh
mkdir -p frame repos
curl -fsSLo frame/index-v2.json https://f-droid.org/repo/index-v2.json   # ours: sha256 900242f55ff7397aca52ffb25439f21657fbfe8cff23f80528a2725da6ce5faf
python3 census/frame.py frame/index-v2.json frame/frame.json             # updated since 2025-10-21, latest build targets <= 35, source on GitHub/GitLab/Codeberg
python3 census/play.py frame/frame.json out/play.jsonl                  # Play listing by package id: 200 = listed, 404 = not; 1.2 s apart
python3 census/scan.py frame/frame.json repos out/scan.jsonl 6          # default branch, depth 1, blobs up to 2 MB, tests and node_modules skipped
python3 census/analyse.py frame/frame.json out/play.jsonl out/scan.jsonl BP out/census-BP.json
```

The F-Droid index changes daily, so a rerun gives a different frame. `scan.py` searches `.java` and `.kt` files for `(override\s+fun|void)\s+onBackPressed\s*\(` and `KEYCODE_BACK`, skipping lines that start a comment, and reads `enableOnBackInvokedCallback` from manifests and the highest `targetSdk` number from Gradle files. `analyse.py` counts an app as at risk when it is listed on Play, its default branch does not target 36 or more (or the target cannot be read), it matches the pattern, and its manifest does not set `enableOnBackInvokedCallback` either way. We then read every match by hand and removed 4 that are not Android back handlers (two game-engine screen methods and two key maps); that leaves 23 Activity `onBackPressed()` overrides and 2 that use only `KEYCODE_BACK`.

[`results/census-counts.json`](results/census-counts.json) has our counts. We do not publish the per-app list.

## Check the note against these files

```sh
python3 check.py
```

It rebuilds the note's table from the two matrix files, the lint findings from the two XML reports, the Cordova double fire from the marker log, and the census figures from `census-counts.json`, and exits 1 if any differs from the note.

## Licence

MIT (see `LICENSE`) for our test app, scripts, results and text. The Android SDK, system images, Gradle, Cordova and the F-Droid index are not included; each has its own terms.
