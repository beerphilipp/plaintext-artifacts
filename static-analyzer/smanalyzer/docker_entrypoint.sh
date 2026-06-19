#!/bin/bash
#
# Script: docker_entrypoint.sh
#
# Description:
#   Runs parallel analysis of APK files using the the manifest analyzer in a Docker container.
#
# Usage:
#   ./docker_entrypoint.sh <APK_DIR> <OUTPUT_DIR> <PARALLELISM>
#
# Arguments:
#   APK_DIR       Directory containing APK files to analyze.
#   OUTPUT_DIR    Directory in which to create `results/` and `logs/` subdirectories and save the results to.
#   PARALLELISM   Number of parallel worker processes to use.
#
# Requirements:
#   - GNU Parallel (`parallel`) must be installed.
#   - `smanalyzer` binary must be on PATH.
#
# Example:
#   ./docker_entrypoint.sh /data/apks /data/output 4
#

if [[ $# -ne 3 ]]; then
    echo "Usage: $0 <APK_DIR> <OUTPUT_DIR> <PARALLELISM>"
    echo "  APK_DIR: Directory containing APK files to analyze."
    echo "  OUTPUT_DIR: Directory to store the analysis results."
    echo "  PARALLELISM: Number of parallel processes to run."
    echo "Example: $0 /path/to/apks /path/to/output 4"
    exit 1
fi

APK_DIR=$1
OUTPUT_DIR=$2
PARALLELISM=$3

RESULT_DIR="$OUTPUT_DIR/output"
LOG_DIR="$OUTPUT_DIR/logs"

if [[ ! -d "$APK_DIR" ]]; then
    echo "APK_DIR does not exist"
    exit 1
fi

if ! mkdir -p "$LOG_DIR"; then
    echo "ERROR: Failed to create log directory '$LOG_DIR'."
    exit 1
fi

if ! mkdir -p "$RESULT_DIR"; then
    echo "ERROR: Failed to create result directory '$RESULT_DIR'."
    exit 1
fi

# Run the analysis in parallel on all APK files in the specified directory
find "$APK_DIR" -mindepth 1 -maxdepth 1 -exec realpath {} \; | parallel --joblog "$LOG_DIR/joblog.log" \
         --results "$LOG_DIR" \
         --resume \
         --progress \
         --eta \
         --jobs "$PARALLELISM" \
         smanalyzer analyze --app {} --out "$RESULT_DIR"

smanalyzer cleartext --out "$RESULT_DIR"