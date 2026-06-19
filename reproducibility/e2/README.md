# Experiment 2 — Static Analysis Pipeline

Runs the static-analysis pipeline (Section 4) on a small randomly-selected sample of APKs: downloads the APKs from the APK dataset, then runs the manifest analyzer and the bytecode analyzer over them.

The analyzers themselves live in `../../static-analyzer/{smanalyzer,bytecodeanalyzer}/`. See their `README.md` files for details on each tool.

## Requirements

- `docker`
- An SSH key authorized for the APK download host at `~/.ssh/webview_key` (request access from the authors)

## Files

| File                       | Purpose                                                                                  |
|----------------------------|------------------------------------------------------------------------------------------|
| `e2.sh`                    | Main experiment driver.                                                                  |
| `Dockerfile`               | Builds the `webview/apk-downloader` image (Alpine + `rsync` + `openssh-client`).         |
| `docker_download_apks.sh`  | Entrypoint of the downloader image: picks `N` random APKs from the remote host and rsyncs them. |
| `out/`                     | Output directory (created on first run).                                                 |

## Running

```bash
./e2.sh
```

Defaults baked into `e2.sh`:

- `APP_COUNT=10` — number of APKs to download
- `PARALLELISM=4` — parallel jobs for each analyzer
- `SSH_KEY=~/.ssh/webview_key`

Edit these at the top of `e2.sh` if you want a different sample size or concurrency.

## What `e2.sh` does

1. Builds three Docker images:
   - `webview/manifest-analyzer:latest` from `../../static-analyzer/smanalyzer`
   - `webview/bytecode-analyzer:latest` from `../../static-analyzer/bytecodeanalyzer`
   - `webview/apk-downloader:latest` from this directory
2. Runs the downloader (mounting `~/.ssh/webview_key`) to fetch `APP_COUNT` random APKs into `out/apks/`.
3. Runs the manifest analyzer over `out/apks/`, writing per-APK results into `out/manifest/`.
4. Runs the bytecode analyzer over `out/apks/`, writing per-APK results into `out/bytecode/out/` and GNU Parallel logs into `out/bytecode/logs/`.