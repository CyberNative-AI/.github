# Android 16 target-36 edge-to-edge and orientation: reproduction

These are the test app and scripts we ran on 2026-10-24. One change: the log tag and the label text in the test app were renamed to `WINPROBE`, here and in the two lint reports in `results/`; nothing else differs except comments. The scripts expect this folder mounted at `/work` in a container, with the Android SDK in `sdk/`, Gradle in `tools/gradle-8.14.3/` and output in `out/`. The build downloads from Google's Maven repository and Maven Central.

Image, pinned by digest: `eclipse-temurin:17-jdk` = `eclipse-temurin@sha256:fe947d993c32dd9cf651a4353a6ed723c2370b3a9d034ea4cab4775404ea531a` (linux/amd64). The emulator needs `/dev/kvm` on an x86_64 Linux host.

```sh
IMG=eclipse-temurin@sha256:fe947d993c32dd9cf651a4353a6ed723c2370b3a9d034ea4cab4775404ea531a
mkdir -p out tools
curl -fsSLo tools/gradle.zip https://services.gradle.org/distributions/gradle-8.14.3-bin.zip && unzip -q tools/gradle.zip -d tools
bash scripts/fetch_sdk.sh "$PWD/sdk"   # pinned SDK archives from dl.google.com (subject to Google's SDK licence), about 3 GB unpacked
```

`fetch_sdk.sh` is the same script as in our [Back handlers reproduction](../../android-16-target-36-back/reproduce/): platform-tools r37.0.1, emulator 16428233, platforms 35 and 36 (r02), build-tools 36.0.0 and the Google APIs x86_64 system images for API 36 (r07) and API 35 (r09). It writes their sha256 to `ARCHIVES.sha256`.

## 1. Build the test app and lint it

`app/` builds one app in four flavors from the same source: `t35` (targetSdk 35), `t36` (36), `t36prop` (36, plus `src/t36prop/AndroidManifest.xml`, which sets the `android.window.PROPERTY_COMPAT_ALLOW_RESTRICTED_RESIZABILITY` property on `<application>`) and `t36game` (36, plus `android:appCategory="game"` on `<application>`). Android Gradle Plugin 8.11.1, Gradle 8.14.3, compileSdk 36, minSdk 30, no AndroidX. Every screen is a plain `android.app.Activity` with an orange `TextView` at the top of a `FrameLayout`. 800 ms after `onResume` (and after each configuration change) it logs one `WINPROBE` line: orientation, smallest width, the label's screen `top`, the status bar inset, the current and maximum window bounds and how many times an Activity was created.

| Activity | What it does |
|---|---|
| `E0` | no opt-out, no inset handling (control: under the bar wherever edge-to-edge is enforced) |
| `E1` | theme `P.OptOut`: `values-v35/themes.xml` sets `android:windowOptOutEdgeToEdgeEnforcement` to `true`; no inset handling |
| `E2` | no opt-out; the root view is padded by the system bar insets (control: never under the bar) |
| `OU` | no orientation setting (control: follows the device) |
| `O1` | `android:screenOrientation="portrait"` in the manifest |
| `O2` | `setRequestedOrientation(SCREEN_ORIENTATION_PORTRAIT)` in `onCreate` |
| `R1` | `android:resizeableActivity="false"` and `android:maxAspectRatio="1.86"` |

`build.sh` builds the four debug APKs, runs `lintT36Debug` and records the APK hashes and manifest attributes.

```sh
docker run --rm --cpus 6 --memory 6g --memory-swap 6g --pids-limit 4096 -v "$PWD:/work" "$IMG" bash -c '/work/scripts/build.sh > /work/out/build.log 2>&1'
```

`app/app/build.gradle` sets `abortOnError false` in its `lint { ... }` block. Lint reported only warnings, so with the default setting it would not have stopped either. Our reports: [`results/lint-t36.txt`](results/lint-t36.txt) and [`results/lint-t36.xml`](results/lint-t36.xml). Our APK hashes and manifest attributes: `results/APK.sha256`, `results/badging.txt`.

## 2. Run every screen on four emulators

`device.sh NAME API WIDTH HEIGHT DENSITY phone|tablet` creates a fresh emulator, turns animations and auto-rotate off and installs the four flavors. It first finds which rotation puts the device in landscape (the first of `user_rotation` 0 and 1 under which `OU` reports landscape). Then, twice per cell:

- phone: `E0`, `E1`, `E2` at `t35` and `t36`, started in portrait, with a screenshot in the first run; `OU`, `O1`, `O2`, `R1` at `t35` and `t36`, started in landscape and then rotated to portrait;
- tablet: `OU`, `O1`, `O2`, `R1` in all four flavors, started in landscape and then rotated to portrait.

Each cell force-stops the app, starts the Activity, waits 4 s and writes one line to `out/cells-NAME.jsonl` with the `WINPROBE` line at the start (`start`) and, where there is a rotation, the last line after it (`after`).

```sh
docker run --rm --cpus 6 --memory 12g --memory-swap 12g --pids-limit 4096 --device /dev/kvm -v "$PWD:/work" "$IMG" bash -c '
  apt-get -qq update; apt-get -qq install -y libpulse0 libnss3 libxcomposite1 libxcursor1 libxi6 libxtst6 libasound2t64 libgl1 libdrm2 libxkbfile1 libxdamage1 libxrandr2 libxkbcommon0 libbsd0 libgbm1
  /work/scripts/device.sh P36 36 1080 2400 420 phone
  /work/scripts/device.sh T36 36 2560 1600 320 tablet
  /work/scripts/device.sh P35 35 1080 2400 420 phone
  /work/scripts/device.sh T35 35 2560 1600 320 tablet'
python3 score.py out
```

`score.py` turns each cell into the readouts the note uses: under the bar = label `top` smaller than the status bar inset; orientation at start; full screen = window bounds equal the maximum bounds; recreated = more Activity creations after the rotation than before. It also runs the validity checks we fixed before the run: on each phone, `E0` under the bar and `E2` never under it at both targets, and `O1` portrait at both targets; on each tablet, `OU` landscape in every flavor and `O1` portrait at target 35.

Our results: `results/cells-*.jsonl`, emulator builds in `results/device-*.txt`. What happened in our run:

- Our first tablet run stopped part-way: with an 8 GB container limit the emulator was killed for lack of memory. We raised the limit to 12 GB (the command above), added a 60 s timeout to every `adb` call and reran the tablet in full on a fresh emulator. The interrupted run is kept as `results/cells-T36-run1.jsonl`; the 23 cells it completed agree with the rerun. The note uses the rerun only.
- The Android 15 phone image never reported landscape under either rotation, so that phone fails the landscape check and its orientation cells are not used. Its edge-to-edge cells start in portrait and involve no rotation; the note reports them for Android 15.
- `R1` does not test what we meant it to: its `maxAspectRatio` of 1.86 is wider than the tablet's 1.6, so it fills the screen in every flavor. The note does not use it.
- The tablet screenshots show an emulator "System UI isn't responding" dialog, so we do not use them. The readouts come from the app's own measurements and are not affected.

The note's illustration combines the first-run screenshots of `E1` at `t35` and `t36` on the Android 16 phone, scaled to 270 × 600 each, with the label text covered by the label's own orange.

## 3. Census

Needs Python 3 and `git`. It starts from the frame of our Back handlers note, so first build that frame with the census scripts in [its reproduction folder](../../android-16-target-36-back/reproduce/) (section 5): `frame.py`, `play.py`, `scan.py` and `analyse.py ... BP out/census-BP.json`. Then:

```sh
python3 census/census.py out/census-BP.json repos-windows out/census.jsonl onplay 6   # clones the Play-listed rows again (depth 1, blobs up to 2 MB)
python3 census/analyse.py out/census.jsonl > out/census.score.json
```

The F-Droid index changes daily and default branches move, so a rerun gives a different frame and different counts. `census.py` never checks out or runs anything from the repositories; it reads blobs as text, skips test folders, `node_modules` and lines that start a comment, and looks for:

- the opt-out: an `item` named `windowOptOutEdgeToEdgeEnforcement` set to `true` in `res/values*/*.xml`;
- a lock: `screenOrientation` with one of the eight portrait or landscape values, `resizeableActivity="false"` or a min/max aspect ratio in a manifest; `setRequestedOrientation` or `requestedOrientation =` with one of those values in Java or Kotlin; Flutter `setPreferredOrientations(`; a Cordova `Orientation` preference; an Expo `"orientation"` of portrait or landscape;
- the escapes: `PROPERTY_COMPAT_ALLOW_RESTRICTED_RESIZABILITY` and `appCategory="game"`;
- the target: the highest `targetSdk` number in Gradle files and version catalogs.

`analyse.py` counts an app when its target is 35 or lower or cannot be read, and it matches the opt-out, or matches a lock without either escape. We then read the target of every match by hand, through version catalogs, root-project variables and CMake defaults. That moved 1 opt-out app and 4 lock apps to target 36 or higher, and left 1 lock app whose target is chosen at build time. We also followed each opt-out theme to where the app applies it, and looked up the F-Droid category of each lock app.

[`results/census-counts.json`](results/census-counts.json) has both the pattern counts and the counts after reading. We do not publish the per-app list.

## Check the note against these files

```sh
python3 check.py
```

It rebuilds both of the note's tables from the cell files, checks the lint report (no finding about the opt-out, no Error, the three orientation warnings) and the census figures in `census-counts.json`, and exits 1 if any differs from the note.

## Licence

MIT (see `LICENSE`) for our test app, scripts, results, illustration and text. The Android SDK, system images, Gradle and the F-Droid index are not included; each has its own terms.
