# smanalyzer — Static Manifest Analyzer

Python tool that performs static analysis of an Android APK's manifest and resources, extracting application metadata, exported components, the network security configuration, and producing a Fastbot configuration used by later stages of the pipeline. A second `cleartext` step aggregates the cleartext-traffic policy from the previously produced output.

## Build

The recommended way to run `smanalyzer` is via Docker.

```bash
docker build -t smanalyzer .
```

To install locally instead (requires Python ≥ 3.10 and a JRE):

```bash
pip install .
```

This installs the `smanalyzer` console script.

## Usage

### Docker

```bash
docker run --rm \
    -v /path/to/apks:/data/apks \
    -v /path/to/output:/data/output \
    smanalyzer /data/apks /data/output <PARALLELISM>
```

Arguments accepted by the container entrypoint:

| Argument      | Description                                                      |
|---------------|------------------------------------------------------------------|
| `APK_DIR`     | Directory containing APK files (or per-app sub-directories).     |
| `OUTPUT_DIR`  | Output directory; `output/` and `logs/` are created inside it.   |
| `PARALLELISM` | Number of APKs analyzed concurrently via GNU Parallel.           |

The container runs `smanalyzer analyze` on every APK in `APK_DIR`, then runs `smanalyzer cleartext` over the produced output.

### `run.sh` (host execution)

`run.sh` runs `smanalyzer` against a curated list of APKs. It requires `smanalyzer` and `parallel` on `PATH`.

```bash
./run.sh <APK_DIR> <APK_LIST> <OUTPUT_DIR> <LOG_DIR> <PARALLELISM>
```

| Argument      | Description                                                                 |
|---------------|-----------------------------------------------------------------------------|
| `APK_DIR`     | Directory containing the APKs.                                              |
| `APK_LIST`    | Text file with one APK file name per line (extension `.apk` optional).      |
| `OUTPUT_DIR`  | Where per-APK analysis results are written.                                 |
| `LOG_DIR`     | Where GNU Parallel job logs are written.                                    |
| `PARALLELISM` | Number of concurrent analyses.                                              |

### CLI

The `smanalyzer` command exposes three subcommands:

```bash
smanalyzer analyze   --app <APK|APK_DIR> --out <OUTPUT_DIR>
smanalyzer cleartext --out <OUTPUT_DIR>
smanalyzer version   --out <OUTPUT_DIR>
```

- `analyze` — decompiles a single APK (Androguard), runs the manifest analysis, and writes the results into `OUTPUT_DIR/<package_name>/`. `--app` may also point to a directory of split APKs; the base APK is selected automatically.
- `cleartext` — iterates over every per-app sub-directory in `OUTPUT_DIR` and writes a `<package>-cleartext-config.json` derived from the previously produced `*-app-info.json`.

## Output

For each analyzed APK, `OUTPUT_DIR/<package_name>/` contains:

- `<package>-app-info.json` — application metadata, components, permissions, and network-security-config flags.
- `<package>-manifest.xml` — decoded `AndroidManifest.xml`.
- `<package>-fastbot-config.*` — generated intent fuzzing configuration.
- `<package>-cleartext-config.json` — cleartext information produced by `cleartext`.
