# bytecodeanalyzer — WebView Bytecode Analyzer

Soot-based static analyzer that inspects an Android APK's bytecode for WebView-related API usage. The analyzer (`wvanalyzer`) is built into a self-contained JAR (`smanalyzer.jar`) and invoked once per APK; `run.sh` and the Docker entrypoint wrap it in GNU Parallel for batch execution.

## Build

The recommended way to build and run the analyzer is via Docker. The Dockerfile performs a multi-stage Maven build of `wvanalyzer/` and ships the resulting JAR on top of an `eclipse-temurin:11-jre` image.

```bash
docker build -t bytecodeanalyzer .
```

To build the JAR directly:

```bash
mvn -f wvanalyzer/pom.xml clean package -DskipTests
# Produces wvanalyzer/target/wvmc.analyzer-1.0-SNAPSHOT-jar-with-dependencies.jar
```

## Usage

### Docker

```bash
docker run --rm \
    -v /path/to/apks:/data/apks \
    -v /path/to/output:/data/output \
    -v /path/to/logs:/data/logs \
    bytecodeanalyzer /data/apks /data/output /data/logs <PARALLELISM>
```

Arguments accepted by the container entrypoint:

| Argument      | Description                                                          |
|---------------|----------------------------------------------------------------------|
| `APK_DIR`     | Directory containing APK files or per-app sub-directories.           |
| `OUTPUT_DIR`  | Where per-APK analysis results are written.                          |
| `LOG_DIR`     | Where GNU Parallel writes `joblog.log` and per-job stdout/stderr.    |
| `PARALLELISM` | Number of APKs analyzed concurrently.                                |

Each entry directly under `APK_DIR` is analyzed by running:

```bash
java -jar smanalyzer.jar --app <APK_OR_DIR> --out <OUTPUT_DIR>
```

`--resume` is enabled, so re-running the same command skips APKs already recorded in the `joblog.log`.

### `run.sh` (host execution)

Run the analyzer outside Docker. Requires `java`, `parallel`, and a built `analyzer.jar` on `PATH`.

```bash
./run.sh <APK_DIR> <OUTPUT_DIR> <LOG_DIR> <PARALLELISM>
```

The arguments match the Docker entrypoint above.

### Direct JAR invocation

For a single APK:

```bash
java -jar analyzer.jar --app <APK_PATH> --out <OUTPUT_DIR>
```

| Option   | Description                                                            |
|----------|------------------------------------------------------------------------|
| `--app`  | Path to an APK file or to a directory of split APKs.                   |
| `--out`  | Output directory for the analysis results.                             |
