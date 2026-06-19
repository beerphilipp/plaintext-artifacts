#!/bin/bash

APK_DIR="$1"
OUTPUT_DIR="$2"
LOG_DIR="$3"
PARALLELISM="$4"

if [[ $# -ne 4 ]]; then
    echo "Usage: $0 <APK_DIR> <OUTPUT_DIR> <LOG_DIR> <PARALLELISM>"
    exit 1
fi

echo "APK_DIR: $APK_DIR"
echo "OUTPUT_DIR: $OUTPUT_DIR"
echo "LOG_DIR: $LOG_DIR"
echo "PARALLELISM: $PARALLELISM"

if [[ ! -d "$APK_DIR" ]]; then
    echo "APK_DIR does not exist"
    exit 1
fi

if [[ ! -d "$OUTPUT_DIR" ]]; then
    echo "OUTPUT_DIR does not exist"
    mkdir -p "$OUTPUT_DIR"
fi

if [[ ! -d "$LOG_DIR" ]]; then
    echo "LOG_DIR does not exist"
    mkdir -p "$LOG_DIR"
fi

find "$APK_DIR" -mindepth 1 -maxdepth 1 -exec realpath {} \; | parallel \
         --joblog "$LOG_DIR/joblog.log" \
         --results "$LOG_DIR" \
         --resume \
         --progress \
         --eta \
         --jobs "$PARALLELISM" \
         java -jar analyzer.jar --app {} --out "$OUTPUT_DIR"

