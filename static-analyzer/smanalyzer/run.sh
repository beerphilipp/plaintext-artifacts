#!/bin/bash

APK_DIR="$1"
APK_LIST="$2"
OUTPUT_DIR="$3"
LOG_DIR="$4"
PARALLELISM="$5"

if [[ $# -ne 5 ]]; then
    echo "Usage: $0 <APK_DIR> <APK_LIST> <OUTPUT_DIR> <LOG_DIR> <PARALLELISM>"
    exit 1
fi

echo "APK_DIR: $APK_DIR"
echo "APK_LIST: $APK_LIST"
echo "OUTPUT_DIR: $OUTPUT_DIR"
echo "LOG_DIR: $LOG_DIR"
echo "PARALLELISM: $PARALLELISM"

if [[ ! -d "$APK_DIR" ]]; then
    echo "APK_DIR does not exist"
    exit 1
fi

if [[ ! -f "$APK_LIST" ]]; then
    echo "APK_LIST does not exist"
    exit 1
fi

if [[ ! -d "$OUTPUT_DIR" ]]; then
    mkdir -p "$OUTPUT_DIR"
fi

if [[ ! -d "$LOG_DIR" ]]; then
    mkdir -p "$LOG_DIR"
fi

if ! command -v smanalyzer &> /dev/null; then
    echo "smanalyzer could not be found"
    exit 1
fi

echo "Reading APKs ..."
apk_paths=()

while IFS= read -r apk; do
    if [[ -e "$APK_DIR/$apk" ]]; then
        apk_paths+=("$(realpath "$APK_DIR/$apk")")
    elif [[ -e "$APK_DIR/$apk.apk" ]]; then
    # add it to apk_paths
        apk_paths+=("$(realpath "$APK_DIR/$apk.apk")")
    else
        echo "APK $apk does not exist in $APK_DIR"
        exit 1
    fi
done < "$APK_LIST"

echo "Found ${#apk_paths[@]} APKs to analyze."

printf "%s\n" "${apk_paths[@]}" | parallel \
         --joblog "$LOG_DIR/joblog.log" \
         --results "$LOG_DIR" \
         --resume \
         --progress \
         --eta \
         --jobs "$PARALLELISM" \
         smanalyzer analyze --app {} --out "$OUTPUT_DIR"

