# Artifacts: Plain Text, Plain Risks: Measuring and Understanding HTTP Inclusion in Android WebViews at Scale

This repository contains the artifacts accompanying the USENIX Security '26 paper *Plain Text, Plain Risks: Measuring and Understanding HTTP Inclusion in Android WebViews at Scale*.

The database snapshot (`mongodb_snapshot.zip`) and the Google Play crawl database (`gplay.sqlite.zip`) are published at <https://doi.org/110.5281/zenodo.20393171>.

## Repository Structure

| Path                                              | Description                                                                                                  | Paper section |
|---------------------------------------------------|--------------------------------------------------------------------------------------------------------------|---------------|
| [`http-content-comparison/`](./http-content-comparison) | Android app + Express server used to compare how WebView and mobile browsers handle HTTP (mixed) content.    | Section 3     |
| [`static-analyzer/`](./static-analyzer)           | Static analysis pipeline: the manifest analyzer (`smanalyzer`) and the bytecode analyzer (`bytecodeanalyzer`). | Section 4.2   |
| [`ui-interactor/`](./ui-interactor)               | Dynamic UI instrumenter (`danalyzer`) used to drive apps and record WebView API/network events.              | Section 4.3   |
| [`webview-provider/`](./webview-provider)         | Pre-built instrumented WebView APKs (`TrichromeLibrary6432.apk`, `TrichromeWebView6432.apk`) and the source patch (`diff.patch`). | Section 4.3   |
| [`apk-download/`](./apk-download)                 | Modified `apkeep` used to crawl APKs from Google Play.                                                       | Section 4.1   |
| [`evaluation_scripts/`](./evaluation_scripts)     | Jupyter notebooks that regenerate the macros, figures, and tables in Section 5 from the measurement database. | Section 5     |
| [`survey/`](./survey)                             | Developer survey questionnaire.                                                                              | Section 7     |
| [`reproducibility/`](./reproducibility)           | Scripts for the artifact-evaluation experiments E1–E3 plus `basic_test.sh`.                                 | -             |

Each subdirectory contains its own `README.md` with detailed usage instructions.

## Hardware & Software Requirements

- **Host:** macOS 26.5 on Apple Silicon (the APK dataset is ARM-only, so an ARM host is required to run the Android emulator). Minimum 16 GB RAM and 250 GB free disk.
- **Docker** — <https://docker.com/get-started>
- **Java (recent JRE/JDK)** — <https://www.java.com/en/download/manual.jsp>
- **Android Studio** — <https://developer.android.com/studio>. Under *Tools → SDK Manager → SDK Tools* install *Android SDK Command-line Tools*, *Android Emulator*, and *Android SDK Platform-Tools*.

## Getting Started

1. **Clone this repository.**

   ```sh
   git clone https://github.com/beerphilipp/plaintext-artifacts.git
   ```

2. **Download and extract the database snapshots** (`mongodb_snapshot.zip`, `gplay.sqlite.zip`) from <https://doi.org/110.5281/zenodo.20393171>.

3. **APK dataset access.** Due to the size of the dataset and legal/regulatory restrictions, the raw APKs cannot be publicly hosted. Reviewers received an SSH key; save it to `~/.ssh/webview_key` and run `chmod 600 ~/.ssh/webview_key`. Other researchers can request access by contacting the authors.

4. **Install the dependencies** listed above.

5. **Sanity-check the setup.** Start an emulator and run the basic test:

   ```sh
   ./reproducibility/e1/start_emulator.sh
   ./reproducibility/basic_test.sh
   ```

   The script builds the Docker images, verifies that the emulator is running, and verifies that the SSH key is in place. It should print **OK**.

## Reproducing the Paper

The three artifact-evaluation experiments are driven by scripts under `reproducibility/`. Each experiment has its own `README.md` with full details.

| Experiment | Claim                          | Driver                       | Approx. budget                            |
|------------|--------------------------------|------------------------------|-------------------------------------------|
| **E1**     | WebView HTTP / mixed-content behavior (C1, Section 3, Table 1) | [`reproducibility/e1/e1.sh`](./reproducibility/e1) | 30 human-min + 20 compute-min + 20 GB disk |
| **E2**     | Static analysis pipeline is functional (C2, Section 4.2) | [`reproducibility/e2/e2.sh`](./reproducibility/e2) | 10 human-min + 20 compute-min + 20 GB disk |
| **E3**     | Measurement results are reproducible (C3, Section 5) | [`reproducibility/e3/e3.sh <mongodb_snapshot> <gplay_db>`](./reproducibility/e3) | 1.5 human-h + 5 compute-h + 200 GB disk    |

E3 starts a MongoDB / Jupyter Docker stack; open <http://localhost:8888> and run the notebooks in `evaluation_scripts/` in ascending order. The artifact appendix contains a notebook-cell-to-paper-section mapping.

## Reusability

The components are designed to be reusable beyond the experiments in this repository:

- `static-analyzer/smanalyzer` and `static-analyzer/bytecodeanalyzer` can be run as standalone Docker images on any APK directory.
- `ui-interactor/danalyzer` is a standalone Python CLI that can drive any app on a connected device or emulator.
- `webview-provider/` ships pre-built APKs of the instrumented WebView so it can be deployed without rebuilding Chromium.
- `http-content-comparison/` (server + Android app) can be reused to compare HTTP/mixed-content handling in any other Android browser or WebView client.
