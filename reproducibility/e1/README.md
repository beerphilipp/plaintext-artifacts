# Experiment 1 — WebView Mixed-Content Behavior

Reproduces the WebView portion of Section 3: launches the Android WebView with three different mixed-content modes and three different load paths against a controlled HTTPS server that serves different content over HTTP vs. HTTPS, so reviewers can confirm which resources the WebView actually loaded.

The components exercised by this experiment live in `../../http-content-comparison/` — see that directory's `README.md` for details on the server endpoints, the test app, and the supported intent extras.

## Requirements

- `adb` on `PATH` (Android SDK platform-tools)
- `docker`
- A running Android emulator (use `./start_emulator.sh`, which creates `webview_emulator` on API 36)
- `ANDROID_HOME` set (only needed for `start_emulator.sh`)

## Files

| File                                          | Purpose                                                                                |
|-----------------------------------------------|----------------------------------------------------------------------------------------|
| `e1.sh`                                       | Main experiment driver (see flow below).                                               |
| `start_emulator.sh`                           | Creates and launches the `webview_emulator` AVD (Pixel 6a, API 36).                    |
| `com.google.android.webview_142.apk`          | Bundled WebView 142 APK (installed if the emulator's WebView is not 142.x).            |
| `com.google.android.trichromelibrary_142.apk` | Trichrome library required by the WebView 142 APK.                                     |

## Running

```bash
# Terminal 1 — start the emulator
./start_emulator.sh

# Terminal 2 — once the emulator is booted
./e1.sh
```

## What `e1.sh` does

1. Verifies that `adb` and `docker` are available and a device is connected and fully booted.
2. Checks the active WebView version; if it is not 142.x, installs the two bundled APKs so the test runs against the same WebView build used in the paper.
3. Builds and starts the `webview/mixed-content-server` container (ports 80 and 443).
4. Maps `mixed-content.test → 10.0.2.2` in the emulator's `/etc/hosts` (via `adb root` / `adb remount`) so the WebView can reach the host-side server.
5. Copies the container-generated `cert.pem` to `/sdcard/Download/mixed-content-server.crt` on the device.
6. **Manual step:** install the CA cert via *Settings → Security & privacy → More security & privacy → Encryption & credentials → Install a certificate → CA certificate → Install anyway → `mixed-content-server.crt`*.
7. Builds the `webview/mc-app` Docker image, extracts the signed APK to `out/app/`, and installs it on the device.
8. Runs five sub-experiments, each launching `com.test.httpcontenttester/.MainActivity` with a different combination of load path and `mc` (mixed-content mode), and prints the expected on-screen result for the operator to confirm.

| #   | Load path             | `mc` mode                                  |
|-----|-----------------------|--------------------------------------------|
| 1   | `loadUrl` over HTTPS  | `0` — `MIXED_CONTENT_ALWAYS_ALLOW`         |
| 2   | `loadUrl` over HTTPS  | `1` — `MIXED_CONTENT_NEVER_ALLOW`          |
| 3   | `loadUrl` over HTTPS  | `2` — `MIXED_CONTENT_COMPATIBILITY_MODE`   |
| 4   | Local file            | `1` — `MIXED_CONTENT_NEVER_ALLOW`          |
| 5   | `loadData`            | `1` — `MIXED_CONTENT_NEVER_ALLOW`          |

Press Enter after each sub-experiment to proceed to the next sub-experiment.
