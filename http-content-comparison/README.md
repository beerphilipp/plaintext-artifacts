# HTTP Content Handling Comparison

Tooling for the experiment in Section 3 of the paper, which compares how Google Chrome, Mozilla Firefox, Brave, and Android WebView handle HTTP (mixed) content. The artifact has two components:

| Component                | Description                                                                                                  |
|--------------------------|--------------------------------------------------------------------------------------------------------------|
| `mixed-content-server/`  | Node.js / Express server that serves the same set of resources over both HTTP and HTTPS, returning a different payload depending on the request scheme so it is visible whether the client actually loaded the HTTP variant. |
| `content-tester-app/`    | Android app embedding a `WebView`. The activity is parameterized via intent extras so different load paths and mixed-content modes can be exercised from `adb`. |

For a fully scripted, end-to-end run see `reproducibility/e1/e1.sh` (Experiment 1 of the artifact). The sections below document the components individually; the final section summarizes the E1 flow.

## 1. Mixed-Content Server

### Build & run

The container generates a self-signed certificate for `mixed-content.test` at build time (see `mixed-content-server/Dockerfile`) — no certificate has to be provided by the user.

Docker (used by E1):

```bash
cd mixed-content-server
docker build -t webview/mixed-content-server:latest .
docker run -d --name mixed-content-server -p 80:80 -p 443:443 \
    webview/mixed-content-server:latest
```

Local Node (requires `key.pem` and `cert.pem` next to `server.js`):

```bash
cd mixed-content-server
npm install
npm start            # HTTP on :80, HTTPS on :443
```

Docker Compose is also provided (`docker-compose.yml`).

### Endpoints

`server.js` returns a different file depending on whether the request was made over HTTP or HTTPS so it is unambiguous which variant the client loaded:

| Path                     | HTTP response          | HTTPS response          |
|--------------------------|------------------------|-------------------------|
| `/`                      | `index_http.html`      | `index_https.html`      |
| `/redir`                 | `empty_http.html`      | `empty_https.html`      |
| `/static/image.png`      | `static/http.png`      | `static/https.png`      |
| `/static/image-small.png`| `static/http-small.png`| `static/https-small.png`|
| `/static/audio.mp3`      | `static/http.mp3`      | `static/https.mp3`      |
| `/static/video.mp4`      | `static/http.mp4`      | `static/https.mp4`      |
| `/static/script.js`      | `static/http.js`       | `static/https.js`       |
| `/static/style.css`      | `static/http.css`      | `static/https.css`      |
| `/static/text.txt`       | `static/http.txt`      | `static/https.txt`      |
| `/static/font.woff2`     | `static/http.woff2`    | `static/https.woff2`    |
| `/static/beacon`         | `200 OK` (logged)      | `200 OK` (logged)       |

## 2. Content Tester App

Android app under `content-tester-app/`. It can be built either through Android Studio or — as in E1 — through the bundled `Dockerfile`, which produces a debug-signed APK at `app/build/outputs/apk/debug/app-debug.apk`:

```bash
cd content-tester-app
docker build -t webview/mc-app:latest .
mkdir -p out
docker run --rm -v "$PWD/out:/apk-output" webview/mc-app
adb install -r out/mixed-content-test.apk
```

On Apple Silicon the Android SDK is x86-only, so pass `--platform=linux/amd64` to both `docker build` and `docker run` (E1 does this automatically).

### Intent extras

The activity (`com.test.httpcontenttester/.MainActivity`) reads intent extras and configures the embedded `WebView` accordingly:

| Extra           | Effect                                                                                                  |
|-----------------|---------------------------------------------------------------------------------------------------------|
| `mc`            | Mixed-content mode: `0` = `MIXED_CONTENT_ALWAYS_ALLOW`, `1` = `MIXED_CONTENT_NEVER_ALLOW`, `2` = `MIXED_CONTENT_COMPATIBILITY_MODE`. |
| `nav`           | If `"1"`, navigation is allowed by the `WebViewClient`.                                                 |
| `url`           | URL to load via `loadUrl`.                                                                              |
| `data`          | If set, content is loaded via `loadData` instead of `loadUrl`.                                          |
| `data_base_url` | If set, content is loaded via `loadDataWithBaseURL` using this base URL.                                |
| `file`          | If set, content is loaded from a local file bundled with the app.                                       |

### Launching the activity

```bash
# loadUrl
adb shell am start -n com.test.httpcontenttester/.MainActivity \
    --es url "https://mixed-content.test" --es mc "<mc>" --es nav "1"

# loadData
adb shell am start -n com.test.httpcontenttester/.MainActivity \
    --es data "1" --es mc "<mc>" --es nav "1"

# loadDataWithBaseURL
adb shell am start -n com.test.httpcontenttester/.MainActivity \
    --es data_base_url "<base_url>" --es mc "<mc>"

# Local file
adb shell am start -n com.test.httpcontenttester/.MainActivity \
    --es file "1" --es mc "<mc>" --es nav "1"
```

`<mc>` is `0`, `1`, or `2` (see above).

## End-to-end via E1 (`reproducibility/e1/e1.sh`)

E1 automates the full setup against an Android emulator. The script:

1. Waits for an `adb` device and verifies that the active WebView is version 142.x. If not, it installs the two bundled APKs (`com.google.android.trichromelibrary_142.apk`, `com.google.android.webview_142.apk`) so the experiment runs against the same WebView build used in the paper.
2. Builds and starts the `webview/mixed-content-server` container (ports 80/443).
3. Writes `10.0.2.2 mixed-content.test` to `/etc/hosts` on the emulator (via `adb root`/`adb remount`) so requests to `https://mixed-content.test` from the WebView reach the host-side container at `10.0.2.2`.
4. Copies the container-generated `cert.pem` out of the server container and pushes it to `/sdcard/Download/mixed-content-server.crt` on the device. **You then have to install the CA certificate manually** via *Settings → Security & privacy → More security & privacy → Encryption & credentials → Install a certificate → CA certificate → Install anyway*, then pick `mixed-content-server.crt` from Downloads.
5. Builds `webview/mc-app`, extracts the signed APK, and installs it.
6. Runs five sub-experiments, each launching `MainActivity` with a different combination of load path and `mc` mode, and prints the expected on-screen output so the operator can confirm the WebView behavior.

The five sub-experiments are:

| #   | Load path             | `mc` mode                          |
|-----|-----------------------|-------------------------------------|
| 1   | `loadUrl` over HTTPS  | `0` — `MIXED_CONTENT_ALWAYS_ALLOW`        |
| 2   | `loadUrl` over HTTPS  | `1` — `MIXED_CONTENT_NEVER_ALLOW`         |
| 3   | `loadUrl` over HTTPS  | `2` — `MIXED_CONTENT_COMPATIBILITY_MODE`  |
| 4   | Local file            | `1` — `MIXED_CONTENT_NEVER_ALLOW`         |
| 5   | `loadData`            | `1` — `MIXED_CONTENT_NEVER_ALLOW`         |

Run it from a separate terminal after starting the emulator with `reproducibility/e1/start_emulator.sh`:

```bash
cd reproducibility/e1
./e1.sh
```
