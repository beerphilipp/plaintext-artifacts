# UI Interactor

The UI Interactor drives Android apps on a device or emulator while recording WebView API calls and WebView network traffic. It ships as the `danalyzer` Python package and uses a Monkey-style fuzzer (with optional intent fuzzing) to explore the app. A manual mode is also provided for interactive exploration.

The recorded API/network logs require the instrumented WebView provider from `../webview-provider/` to be installed and selected as the system WebView.

## Layout

| Path                | Description                                                                                  |
|---------------------|----------------------------------------------------------------------------------------------|
| `danalyzer/`        | The `danalyzer` Python package (CLI entrypoint, Monkey runner, manual runner, net debugger). |
| `dependency/aaem/`  | Local dependency: `aaem` (ADB / emulator interaction library) used by `danalyzer`.           |

## Installation

Requires Python ≥ 3.10 and `adb` on `PATH`. Install `aaem` first, then `danalyzer`:

```sh
pip install ./dependency/aaem
pip install ./danalyzer
```

This installs the `danalyzer` console script.

## Usage

```sh
danalyzer monkey -d <DEVICE> -a <APP> -o <OUT> -t <SECONDS> -c <CONFIG_DIR>
danalyzer manual -d <DEVICE> -a <APP> -o <OUT> -t <SECONDS>
```

Common options:

| Option           | Description                                                                                                  |
|------------------|--------------------------------------------------------------------------------------------------------------|
| `-d, --device`   | Device ID, comma-separated list of IDs, or an AVD prefix (e.g. `avd-*`).                                     |
| `-a, --app`      | Path to the APK, or to a directory of split APKs.                                                            |
| `-o, --out`      | Output directory for the recorded logs.                                                                      |
| `-t, --duration` | Test duration in seconds.                                                                                    |

`monkey` additionally requires `-c/--config-dir`, the directory holding per-package intent-fuzzing configs (`<package>/<package>-fastbot-config.json`) produced by `smanalyzer` (see `../static-analyzer/smanalyzer/`).

Example:

```sh
danalyzer monkey \
    -d emulator-5554 \
    -a /apks/com.example.app.apk \
    -o ./out \
    -t 300 \
    -c /smanalyzer-out
```

## Prerequisites on the device

- The custom WebView provider (`TrichromeLibrary6432.apk` + `TrichromeWebView6432.apk`) from `../webview-provider/` must be installed and set as the system WebView so API calls and network events are recorded.
- The device must be reachable via `adb` (USB or emulator).
