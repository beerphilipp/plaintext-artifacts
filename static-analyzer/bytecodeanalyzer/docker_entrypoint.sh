#!/bin/bash
#
# Usage:
#   ./docker_entrypoint.sh <JAR> <APK_DIR> <OUTPUT_DIR> <LOG_DIR> <PARALLELISM>
#
# The first argument (JAR) is supplied by the Dockerfile ENTRYPOINT.

set -euo pipefail

if [[ $# -ne 5 ]]; then
    echo "Usage: $0 <JAR> <APK_DIR> <OUTPUT_DIR> <LOG_DIR> <PARALLELISM>"
    exit 1
fi

JAR=$1
APK_DIR=$2
OUTPUT_DIR=$3
LOG_DIR=$4
PARALLELISM=$5

if [[ ! -f "$JAR" ]]; then
    echo "JAR $JAR does not exist"
    exit 1
fi

if [[ ! -d "$APK_DIR" ]]; then
    echo "APK_DIR $APK_DIR does not exist"
    exit 1
fi

mkdir -p "$OUTPUT_DIR" "$LOG_DIR"

find "$APK_DIR" -mindepth 1 -maxdepth 1 -exec realpath {} \; | parallel \
         --joblog "$LOG_DIR/joblog.log" \
         --results "$LOG_DIR" \
         --resume \
         --progress \
         --eta \
         --jobs "$PARALLELISM" \
         java -jar "$JAR" --app {} --out "$OUTPUT_DIR"
