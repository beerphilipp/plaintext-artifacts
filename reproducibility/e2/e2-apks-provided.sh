#!/usr/bin/env bash
#
# Script: e2.sh
#
# Description:
#   Executes experiment 2.
#
# Usage:
#   ./e2.sh

abort() {
    echo "ERROR: $1" >&2
    exit 1
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
MANIFEST_ANALYZER_DIR="${ROOT_DIR}/static-analyzer/smanalyzer"
BYTECODE_ANALYZER_DIR="${ROOT_DIR}/static-analyzer/bytecodeanalyzer"

MANIFEST_ANALYZER_IMAGE="webview/manifest-analyzer:latest"
BYTECODE_ANALYZER_IMAGE="webview/bytecode-analyzer:latest"
DOWNLOADER_IMAGE="webview/apk-downloader:latest"

command -v docker >/dev/null || abort "Docker is not installed. Please install it to run this script."

[[ -d "${MANIFEST_ANALYZER_DIR}" ]] || abort "Manifest analyzer directory not found: ${MANIFEST_ANALYZER_DIR}"
[[ -d "${BYTECODE_ANALYZER_DIR}" ]] || abort "Bytecode analyzer directory not found: ${BYTECODE_ANALYZER_DIR}"

echo "=> Building Docker images ..."

echo "  - ${MANIFEST_ANALYZER_IMAGE}"
docker build -t "${MANIFEST_ANALYZER_IMAGE}" "${MANIFEST_ANALYZER_DIR}" >/dev/null 2>&1 || abort "Failed to build manifest analyzer image."

echo "  - ${BYTECODE_ANALYZER_IMAGE}"
docker build -t "${BYTECODE_ANALYZER_IMAGE}" "${BYTECODE_ANALYZER_DIR}" >/dev/null 2>&1 || abort "Failed to build bytecode analyzer image."

echo "  - ${DOWNLOADER_IMAGE}"
docker build -t "${DOWNLOADER_IMAGE}" "${SCRIPT_DIR}" >/dev/null 2>&1 || abort "Failed to build APK downloader image."

echo "  Docker images built successfully."


OUT_DIR="${SCRIPT_DIR}/out"
APK_DIR="${SCRIPT_DIR}/apks"
BYTECODE_OUTPUT_DIR="${OUT_DIR}/bytecode/out"
MANIFEST_OUTPUT_DIR="${OUT_DIR}/manifest"
BYTECODE_LOG_DIR="${OUT_DIR}/bytecode/logs"

APP_COUNT=10
PARALLELISM=4
SSH_KEY="${HOME}/.ssh/webview_key"


[[ -f "${SSH_KEY}" ]] || abort "SSH key not found: ${SSH_KEY}"
mkdir -p "${MANIFEST_OUTPUT_DIR}" \
         "${BYTECODE_OUTPUT_DIR}" "${BYTECODE_LOG_DIR}"
         

#########################
# Run Manifest Analyzer #
#########################

echo ""
echo "=> Running manifest analyzer on ${APK_DIR} ..."
docker run --rm \
    -v "${APK_DIR}:/apks:ro" \
    -v "${MANIFEST_OUTPUT_DIR}:/output" \
    "${MANIFEST_ANALYZER_IMAGE}" \
    /apks /output "${PARALLELISM}" >/dev/null 2>&1

echo "  Manifest analyzer results in ${MANIFEST_OUTPUT_DIR}."



#########################
# Run Bytecode Analyzer #
#########################

echo ""
echo "=> Running bytecode analyzer on ${APK_DIR} ..."
docker run --rm \
    -v "${APK_DIR}:/apks:ro" \
    -v "${BYTECODE_OUTPUT_DIR}:/output" \
    -v "${BYTECODE_LOG_DIR}:/logs" \
    "${BYTECODE_ANALYZER_IMAGE}" \
    /apks /output /logs "${PARALLELISM}" >/dev/null 2>&1

echo "  Bytecode analyzer results in ${BYTECODE_OUTPUT_DIR}."
