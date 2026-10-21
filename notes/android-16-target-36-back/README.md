# Raising targetSdk to 36 for Google Play? Your onBackPressed() override stops being called on Android 16

Run this in your app's source tree before you change the target:

```sh
grep -rnE --include='*.java' --include='*.kt' '(override[[:space:]]+fun|void)[[:space:]]+onBackPressed[[:space:]]*\(|KEYCODE_BACK' .
```

In our test, raising only `targetSdk` from 35 to 36 changed the Back key on an Android 16 emulator in two ways. An Activity's `onBackPressed()` override was not called at all, and the screen closed. An `onKeyDown` handler for `KEYCODE_BACK` ran and returned `true`, but the screen closed anyway. On Android 15, and at target 35, every handler worked as before.

The search also prints `Dialog.onBackPressed()` overrides, which kept working in our test, and lines inside comments.

## Why now

Since 31 August 2026, new apps and app updates on Google Play must target Android 16 (API level 36). Wear OS, Android Automotive OS, Android TV and Android XR apps have lower requirements. Developers could ask for more time, but only until 1 November 2026 ([Play Console Help](https://support.google.com/googleplay/android-developer/answer/11926878): "You will be able to request an extension to November 1, 2026"). After that, an update that still targets 35 cannot be submitted.

Google documents the change in [Android 16's behavior changes](https://developer.android.com/about/versions/16/behavior-changes-16) for apps that target 36: "`onBackPressed` is not called and `KeyEvent.KEYCODE_BACK` is not dispatched anymore." The developer has to move to the newer back APIs or opt out "temporarily". We tested what this does to existing code.

## What we measured

One test app, built three ways from the same source: target 35, target 36, and target 36 with the opt-out line. Each screen intercepts Back in a different way. We sent one Back key press to each screen, twice, on an Android 16 and an Android 15 emulator (measured 2026-10-21).

| How the screen handles Back | Target 35 on Android 16 | **Target 36 on Android 16** | Target 36 + opt-out on Android 16 | Any build on Android 15 |
|---|---|---|---|---|
| `Activity.onBackPressed()` override | handled | **not called, screen closes** | handled | handled |
| `AppCompatActivity.onBackPressed()` override | handled | **not called, screen closes** | handled | handled |
| `Activity.onKeyDown()` returns `true` for `KEYCODE_BACK` | handled | **handler runs, screen closes anyway** | handled | handled |
| `AppCompatActivity.onKeyDown()` for `KEYCODE_BACK` | handled | **handler runs, screen closes anyway** | handled | handled |
| `android.app.Dialog.onBackPressed()` override | handled | handled | handled | handled |
| AndroidX `OnBackPressedCallback` | handled | handled | handled | handled |
| No handler | closes | closes | closes | closes |

Both runs agreed in every cell. Google's text says `KEYCODE_BACK` is no longer dispatched; on the key press we sent, `onKeyDown` did still receive it, but returning `true` no longer kept the user on the screen. We did not test the swipe gesture. A swipe sends no key event, so we expect `onKeyDown` handlers not to run at all there.

## What to do

**Move the logic to `OnBackPressedCallback`.** This is the version that kept working in every cell above:

```java
getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
  @Override public void handleOnBackPressed() {
    // what your onBackPressed() used to do
  }
});
```

It needs AndroidX (`androidx.activity`, which AppCompat includes). Google's [migration guide](https://developer.android.com/guide/navigation/custom-back/predictive-back-gesture#update-custom) says to enable or disable each callback as your screen's state changes, so that it intercepts Back only while it has something to do.

**Or opt out, as a stopgap.** One attribute on `<application>` in `AndroidManifest.xml` restored every handler in our test:

```xml
<application android:enableOnBackInvokedCallback="false" ...>
```

Google calls this a temporary opt-out, so plan the migration anyway. Check whether your manifest already sets it:

```sh
grep -rn --include=AndroidManifest.xml enableOnBackInvokedCallback .
```

**Then test on Android 16.** Testing on an Android 15 device or emulator shows nothing: every handler worked there at both targets.

## Lint warns you only if you run it

With stock settings (Android Gradle Plugin 8.11.1), `./gradlew lint` at target 36 reported `GestureBackNavigation` at Error severity for each `onBackPressed()` override and each `KEYCODE_BACK` handler in our app. At target 35 it reported none of them. A release build with default settings still succeeded at target 36, so nothing stops you from shipping the change without running lint. Lint also flagged the `Dialog.onBackPressed()` override, which still worked in our test.

## Frameworks

**Cordova.** With cordova-android 14.0.1 and only `<preference name="android-targetSdkVersion" value="36" />` added to `config.xml`, the `backbutton` event still fired on Android 16, but the app closed anyway. cordova-android 15.1.0, released in July and targeting 36 by default, kept the app open. On Android 16 it fired `backbutton` twice for each Back key press, and once on Android 15. This is already reported in cordova-android [issue 2028](https://github.com/apache/cordova-android/issues/2028), with a fix in [pull request 2029](https://github.com/apache/cordova-android/pull/2029); both were open on 21 October. If your `backbutton` handler goes back one screen, a single press may go back two until that fix ships.

**React Native.** We did not build a React Native app. In React Native 0.79 and earlier, `ReactActivity` overrides `onBackPressed()` ([v0.79.0 source](https://github.com/facebook/react-native/blob/v0.79.0/packages/react-native/ReactAndroid/src/main/java/com/facebook/react/ReactActivity.java)). Version 0.80.0 adds an `OnBackPressedCallback` for target 36 ([v0.80.0 source](https://github.com/facebook/react-native/blob/v0.80.0/packages/react-native/ReactAndroid/src/main/java/com/facebook/react/ReactActivity.java)). `ReactActivity` extends `AppCompatActivity`, the case our test shows is no longer called, so we expect React Native before 0.80 at target 36 to miss Back presses in JavaScript. That is our reading of the source, not a test.

## How common is it

We took the open-source apps on F-Droid that were updated in the past year and whose latest F-Droid build still targets 35 or lower: 759 apps with source on GitHub, GitLab or Codeberg. 99 of them have a Google Play listing under the same package name (checked 2026-10-21). We read the source of 98 of these on their default branch; the other one could not be cloned. 21 already target 36 there.

23 of the 99 have an Activity `onBackPressed()` override and no `enableOnBackInvokedCallback` setting, and do not target 36 on their default branch. For 4 of these 23 we could not read the target from the build files and counted them as not yet at 36. 2 more intercept only `KEYCODE_BACK`. We read each override. They do real work: go back a page in a WebView, ask about unsaved changes before leaving, close a side drawer or selection mode, or return a result to the previous screen. If one of these apps raises only its target, Back on Android 16 will close the screen instead, going by our test.

These are open-source apps, read from their default branch, not the builds on Google Play. An app's next release may already handle this on another branch. We do not say any of these apps is broken.

## Limits

Android emulators (Google APIs x86_64 images, Android 16 build BE2A.250530.026.F3 and Android 15 build AE3A.240806.043), not phones. One input: the Back key sent with `adb shell input keyevent KEYCODE_BACK`. We did not test the swipe gesture, predictive back animations or manufacturer skins. Two repeats per cell. The census covers open-source F-Droid apps only. Its counts come from a text search of default-branch source, which we then read by hand; Play listings were matched by package name. The React Native result is from reading source. One run on our own hardware; not reproduced by anyone else.

Test app, scripts, raw results and the census tally: [`reproduce/`](reproduce/).

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai. We publish dated corrections here.
