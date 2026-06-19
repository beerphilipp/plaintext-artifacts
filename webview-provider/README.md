# Custom WebView Provider

The dynamic analysis pipeline relies on a custom WebView provider that is instrumented to log all API calls.

## Setup the Device

> We assume a Pixel device, i.e., Pixel 8, running Android 16

- Root the device using [`Magisk`](https://github.com/topjohnwu/Magisk) (see [here](https://topjohnwu.github.io/Magisk/install.html) for instructions).
- Install [`LSPosed`](https://github.com/lsposed/lsposed).
- Install [`CorePatch`](https://github.com/LSPosed/CorePatch) to allow installing the Custom WebView provider.

## Setup the WebView Provider

We provide the pre-built APKs of the custom WebView provider in this directory, so you do not need to build it yourself:

- `TrichromeLibrary6432.apk` — the required Trichrome library
- `TrichromeWebView6432.apk` — the instrumented WebView provider

Install both with `adb` (the Trichrome library must be installed first), then set the custom provider as the system WebView:

```sh
$ adb install -r TrichromeLibrary6432.apk
$ adb install -r TrichromeWebView6432.apk
```

If you prefer to build the provider from source instead, follow the steps below.

### Checkout Chrome 

> This requires a significant amount of disk space. For general checkout and build instructions, check out [this guide](https://chromium.googlesource.com/chromium/src/+/HEAD/docs/android_build_instructions.md). Checking out Chrome is only guaranteed to work on Ubuntu (64-bit Intel). MacOS and Windows for sure do not work. 

We base our custom WebView provider on the commit `269995a8`.

1. **Install Depot Tools and add it to `$PATH`**
```sh
$ git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
$ export PATH=$PATH:<path to depot_tools>
```

2. **Fetch the Chrome Code**
```sh
$ mkdir chromium && cd chromium
$ fetch --nohooks --no-history android
$ cd src && gclient sync --with_branch_heads --with_tags
```

3. **Revert to Specific Commit**
```sh
$ git checkout 269995a8
```

4. **Checkout and Sync Dependencies**
```sh
$ gclient sync -D --force --reset
```

5. **Install Build Dependencies**
```sh
$ build/install-build-deps.sh --android
$ gclient runhooks
$ source build/android/envsetup.sh
```

6. **Apply the Patch**
```sh
$ git apply diff.patch
```

### Configure and Build

1. **Generate Build Configs** 
```sh
$ gn args out/arm64`
```
and use
```
target_os = "android"
target_cpu = "arm64"
system_webview_package_name = "com.google.android.webview"
is_debug = false
is_official_build = true
disable_fieldtrial_testing_config = true
is_component_build = false
is_chrome_branded = false
use_official_google_api_keys = false
android_channel = "stable"
ffmpeg_branding = "Chrome"
proprietary_codecs = true
```

2. **Build**
```sh
$ autoninja -C out/arm64 trichrome_webview_apk
```

3. **Install**
```sh
$ out/arm64/bin/trichrome_webview_apk install
```

4. **Set as WebView provider**
```sh
$ out/arm64/bin/trichrome_webview_apk set-webview-provider
```
