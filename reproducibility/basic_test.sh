#!/usr/bin/env bash
#
# Script: basic_test.sh
#
# Description:
#   Performs a basic test of the artifacts.
#   1. Builds the necessary Docker images.
#   2. Checks if an emulator is running.
#   3. Checks if the SSH key is correctly saved.
#
# Usage:
#   ./basic_test.sh

abort() {
  echo "❌ ERROR: $1" >&2
  exit 1
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/test_output"

MCS_DIR="${ROOT_DIR}/http-content-comparison/mixed-content-server"
APP_DIR="${ROOT_DIR}/http-content-comparison/content-tester-app"
MANIFEST_ANALYZER_DIR="${ROOT_DIR}/static-analyzer/smanalyzer"
BYTECODE_ANALYZER_DIR="${ROOT_DIR}/static-analyzer/bytecodeanalyzer"
DOWNLOADER_DIR="${SCRIPT_DIR}/e2"

if [[ $# -gt 0 ]]; then
  echo "Usage: $0"
  exit 1
fi

# Check if Docker is installed and the Docker daemon is running
if ! command -v docker &> /dev/null; then
  abort "Docker is not installed. Please install Docker and try again."
fi
if ! docker info &> /dev/null; then
  abort "Docker daemon is not running. Please start Docker and try again."
fi

[[ ! -d "${OUTPUT_DIR}" ]] \
  || abort "Output directory ${OUTPUT_DIR} already exists. Please remove it before running the test and try again."

#######################
# Build Docker Images #
#######################

DOCKER_PLATFORM=""
case "$(uname -m)" in
    arm64|aarch64)
        DOCKER_PLATFORM="--platform=linux/amd64"
        ;;
esac

echo "(1/3) Building Docker images ..."

# For E1
echo "--> (E1: i/ii) Building the mixed content server"
docker build -t webview/mixed-content-server:latest "$MCS_DIR" >/dev/null 2>&1 \
    || abort "Failed to build webview/mixed-content-server Docker image"

echo "--> (E1: ii/ii) Building the mixed content test app"
docker build $DOCKER_PLATFORM -t webview/mc-app:latest "$APP_DIR" >/dev/null 2>&1 || abort "Failed to build Docker image 'webview/mc-app'"

# For E2
echo "--> (E2: i/iii) Building the manifest analyzer"
docker build -t webview/manifest-analyzer:latest "$MANIFEST_ANALYZER_DIR" >/dev/null 2>&1 \
    || abort "Failed to build Docker image 'webview/manifest-analyzer'"

echo "--> (E2: ii/iii) Building the bytecode analyzer"
docker build -t webview/bytecode-analyzer:latest "$BYTECODE_ANALYZER_DIR" >/dev/null 2>&1 \
    || abort "Failed to build Docker image 'webview/bytecode-analyzer'"

echo "--> (E2: iii/iii) Building the APK downloader"
docker build -t webview/apk-downloader:latest "$DOWNLOADER_DIR" >/dev/null 2>&1 \
    || abort "Failed to build Docker image 'webview/apk-downloader'"

# For E3
echo "--> (E3: i/i) Building the evaluation script image"
EVAL_DIR="${ROOT_DIR}/evaluation_scripts"
docker build -t webview/jupyter "$EVAL_DIR" >/dev/null 2>&1 \
    || abort "Failed to build Docker image 'webview/jupyter'"


########################
# Check Android device #
########################

echo "(2/3) Checking if an Android device is connected ..."

# Check if adb is installed
if ! command -v adb &> /dev/null; then
  abort "adb is not installed. Please install Android SDK Platform Tools."
fi

# Check if an Android device is connected
if ! adb devices | grep -q "device$"; then
  abort "No emulator is connected. Please start the emulator with './start_emulator.sh'"
fi 

#################
# Check SSH Key #
#################

echo "(3/3) Checking SSH Key..."

# check if the ssk key is located at ~/.ssh/webview_key and if it has correct permissions
SSH_KEY="${HOME}/.ssh/webview_key"

[[ -f "${SSH_KEY}" ]] || abort "SSH key not found at ${SSH_KEY}"

KEY_PERMS="$(stat -f '%Lp' "${SSH_KEY}" 2>/dev/null || stat -c '%a' "${SSH_KEY}" 2>/dev/null)"
[[ "${KEY_PERMS}" == "600" || "${KEY_PERMS}" == "400" ]] \
    || abort "SSH key ${SSH_KEY} has insecure permissions ${KEY_PERMS} (expected 600 or 400). Run: chmod 600 ${SSH_KEY}"


echo "--------------------------------"
echo "OK"
echo "--------------------------------"