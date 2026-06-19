#!/usr/bin/env bash
#
# Script: e1.sh
#
# Description:
#   Executes experiment 1.
#
# Usage:
#   ./e1.sh

abort() {
    echo "ERROR: $1" >&2
    exit 1
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
APP_DIR="${ROOT_DIR}/http-content-comparison/content-tester-app"
APP_DIR_OUTPUT="${SCRIPT_DIR}/out/app"

echo "--------------------------------"
echo "Experiment 1: WebView Comparison"
echo "--------------------------------"

# Check dependencies
command -v adb >/dev/null || abort "ADB is not installed. Please install it to run this script."
command -v docker >/dev/null || abort "Docker is not installed. Please install it to run this script."

# Ensure a device is connected
if [ "$(adb devices | grep -w "device" | wc -l)" -eq 0 ]; then
    abort "No device is connected. Please run reproducibility/e1/start_emulator.sh to start the emulator first."
fi

adb wait-for-device

A=$(adb shell getprop sys.boot_completed | tr -d '\r')

while [ "$A" != "1" ]; do
        sleep 2
        A=$(adb shell getprop sys.boot_completed | tr -d '\r')
done

echo "Device is ready."

############################################
# Installing the proper version of WebView #
############################################

# Read the current active WebView package and version
WEBVIEW_PKG=$(adb shell dumpsys webviewupdate 2>/dev/null \
    | awk -F': ' '/Current WebView package \(name, version\)/ {print $2; exit}' \
    | tr -d '\r()' | awk -F',' '{print $1}' | xargs)

if [ -z "$WEBVIEW_PKG" ]; then
    WEBVIEW_PKG=$(adb shell dumpsys webviewupdate 2>/dev/null \
        | awk -F': ' '/Current WebView package/ {print $2; exit}' \
        | tr -d '\r')
fi

if [ -n "$WEBVIEW_PKG" ]; then
    WEBVIEW_VERSION=$(adb shell dumpsys package "$WEBVIEW_PKG" 2>/dev/null \
        | awk -F'=' '/versionName=/ {print $2; exit}' \
        | tr -d '\r')
    echo "Active WebView: ${WEBVIEW_PKG} (version ${WEBVIEW_VERSION:-unknown})"
else
    echo "WARNING: Could not determine active WebView package." >&2
fi

# Ensure WebView major version is 142; if not, install the bundled APKs
if [[ "$WEBVIEW_VERSION" == 142.* ]]; then
    echo "WebView version is 142.x — no update needed."
else
    echo "WebView version is not 142.x — installing bundled APKs."
    TRICHROME_APK="${SCRIPT_DIR}/com.google.android.trichromelibrary_142.apk"
    WEBVIEW_APK="${SCRIPT_DIR}/com.google.android.webview_142.apk"
    [[ -f "$TRICHROME_APK" ]] || abort "Missing APK: $TRICHROME_APK"
    [[ -f "$WEBVIEW_APK" ]]   || abort "Missing APK: $WEBVIEW_APK"
    adb install -r "$TRICHROME_APK" || abort "Failed to install $TRICHROME_APK"
    adb install -r "$WEBVIEW_APK"   || abort "Failed to install $WEBVIEW_APK"
    echo "WebView 142 APKs installed."
fi

####################################################
# Setting up the server and configuring the device #
####################################################

# Set platform flag for ARM hosts
DOCKER_PLATFORM=""
case "$(uname -m)" in
    arm64|aarch64)
        DOCKER_PLATFORM="--platform=linux/amd64"
        ;;
esac

# Build the mixed-content-server Docker image
MCS_DIR="${ROOT_DIR}/http-content-comparison/mixed-content-server"
[[ -d "$MCS_DIR" ]] || abort "mixed-content-server directory not found at $MCS_DIR"
echo "==> Building mixed-content-server Docker image"
docker build -t webview/mixed-content-server:latest "$MCS_DIR" >/dev/null 2>&1 \
    || abort "Failed to build webview/mixed-content-server Docker image"

echo "==> Starting mixed-content-server container"
docker rm -f mixed-content-server >/dev/null 2>&1 || true
docker run -d --name mixed-content-server \
    -p 80:80 -p 443:443 \
    webview/mixed-content-server:latest \
    || abort "Failed to start mixed-content-server container"

# Updating the /etc/hosts file on the device
echo "10.0.2.2 mixed-content.test" > /tmp/emulator-hosts
adb root  >/dev/null 2>&1 || abort "ADB root failed"
adb remount  >/dev/null 2>&1 || abort "ADB remount failed"
adb push /tmp/emulator-hosts /etc/hosts  >/dev/null 2>&1 || abort "ADB push failed"

# Pushing the certificate to the device
CERT_PEM="/tmp/mixed-content-server-cert.pem"
docker cp mixed-content-server:/app/cert.pem "$CERT_PEM" \
    || abort "Failed to copy cert.pem from mixed-content-server container"

DEVICE_CERT_PATH="/sdcard/Download/mixed-content-server.crt"
adb push "$CERT_PEM" "$DEVICE_CERT_PATH" \
    || abort "Failed to push certificate to $DEVICE_CERT_PATH"



########################################
# Building and installing the test app #
########################################

# Build Docker image
echo "Building the MC App Docker image..."
docker build ${DOCKER_PLATFORM} -t webview/mc-app:latest "$APP_DIR" >/dev/null 2>&1 || abort "Failed to build Docker image 'webview/mc-app'"

# Create output directory
mkdir -p "$APP_DIR_OUTPUT" || abort "Failed to create output directory: ${APP_DIR_OUTPUT}"

echo "Running the MC App Docker container..."
docker run --rm -v "$APP_DIR_OUTPUT:/apk-output" webview/mc-app >/dev/null 2>&1 || abort "Failed to run Docker container"

# Install APK
APK_PATH="${APP_DIR_OUTPUT}/mixed-content-test.apk"
[ -f "$APK_PATH" ] || abort "APK not found at $APK_PATH"
echo "Installing the APK..."
adb install -r "$APK_PATH" >/dev/null 2>&1 || abort "Failed to install APK"

echo ""
echo "ACTION REQUIRED"
echo ""
echo "==> Install the certificate on the device:"
echo "    Settings -> Security & privacy -> More security & privacy -> Encryption & credentials"
echo "    -> Install a certificate -> CA certificate -> Install anyway -> pick mixed-content-server.crt from Downloads."
echo "Press enter when you have finished this step."
read -r 

echo "---------"
echo "EXPERIMENT 1/5"
echo ""
echo "=> Opening 'https://mixed-content.test with setMixedContentMode to MIXED_CONTENT_ALWAYS_ALLOW"
adb shell am start -n com.test.httpcontenttester/.MainActivity --es url "https://mixed-content.test" --es mc "0" --es nav "1"
echo " >> The website should display the following:"
echo ""
echo " >> UPGRADABLE MIXED CONTENT"
echo " >> - An image showing 'HTTP'"
echo " >> - A 30s video showing the earth"
echo " >> - 2 one second audios of a cat miaowing"
echo " >> - Another 30s video showing the earth"
echo ""
echo " >> BLOCKABLE MIXED CONTENT"
echo " >> - A paragraph saying 'Script loaded over HTTP'"
echo " >> - A red text paragraph"
echo " >> - An iframe saying 'HTTP'"
echo " >> - A paragraph saying 'Fetch succeeded over: HTTP"
echo " >> - A paragraph saying 'XHR succeeded over: HTTP"
echo " >> - A background image saying 'HTTP'"
echo " >> - An object tag showing 'served over HTTP'"
echo " >> - A paragraph saying 'Beacon send attempted over HTTP"
echo " >> - A red image"
echo " >> - A text in the Comic Sans font"
echo "-------"
echo "Press enter to continue"
read -r

adb shell am force-stop com.test.httpcontenttester
sleep 1


echo "---------"
echo "EXPERIMENT 2/5"
echo ""
echo "=> Opening 'https://mixed-content.test with setMixedContentMode to MIXED_CONTENT_NEVER_ALLOW"
adb shell am start -n com.test.httpcontenttester/.MainActivity --es url "https://mixed-content.test" --es mc "1" --es nav "1"
echo " >> The website should display the following:"
echo ""
echo " >> UPGRADABLE MIXED CONTENT"
echo " >> - No image"
echo " >> - No video"
echo " >> - No audio"
echo " >> - No audio"
echo " >> - No video"
echo ""
echo " >> BLOCKABLE MIXED CONTENT"
echo " >> - A paragraph saying 'No script was loaded'"
echo " >> - A black text paragraph"
echo " >> - An iframe with no content"
echo " >> - A paragraph saying 'Fetch blocked or network error"
echo " >> - A paragraph saying 'XHR blocked or error"
echo " >> - A paragraph saying 'XHR succeeded over: HTTP"
echo " >> - An empty background image"
echo " >> - An empty object"
echo " >> - A paragraph saying 'Beacon send failed"
echo " >> - No image"
echo " >> - A sans-serif font text"
echo "-------"
echo "Press enter to continue"
read -r

adb shell am force-stop com.test.httpcontenttester
sleep 1


echo "---------"
echo "EXPERIMENT 3/5"
echo ""
echo "=> Opening 'https://mixed-content.test with setMixedContentMode to MIXED_CONTENT_COMPATIBILITY_MODE"
adb shell am start -n com.test.httpcontenttester/.MainActivity --es url "https://mixed-content.test" --es mc "2" --es nav "1"
echo " >> The website should display the following:"
echo ""
echo " >> UPGRADABLE MIXED CONTENT"
echo " >> - An image showing 'HTTP'"
echo " >> - A 30s video showing the earth"
echo " >> - 2 one second audios of a cat miaowing"
echo " >> - Another 30s video showing the earth"
echo " >> - Another 30s video showing the earth"
echo ""
echo " >> BLOCKABLE MIXED CONTENT"
echo " >> - A paragraph saying 'No script was loaded'"
echo " >> - A black text paragraph"
echo " >> - An iframe with no content"
echo " >> - A paragraph saying 'Fetch blocked or network error"
echo " >> - A paragraph saying 'XHR blocked or error"
echo " >> - A paragraph saying 'XHR succeeded over: HTTP"
echo " >> - A background image saying 'HTTP'"
echo " >> - An empty object"
echo " >> - A paragraph saying 'Beacon send failed"
echo " >> - No image"
echo " >> - A sans-serif font text"
echo "-------"
echo "Press enter to continue"
read -r

adb shell am force-stop com.test.httpcontenttester
sleep 1


echo "---------"
echo "EXPERIMENT 4/5"
echo ""
echo "=> Opening file with setMixedContentMode to MIXED_CONTENT_NEVER_ALLOW"
adb shell am start -n com.test.httpcontenttester/.MainActivity --es file "1" --es mc "1" --es nav "1"
echo " >> The website should display the following:"
echo ""
echo " >> UPGRADABLE MIXED CONTENT"
echo " >> - An image showing 'HTTP'"
echo " >> - A 30s video showing the earth"
echo " >> - 2 one second audios of a cat miaowing"
echo " >> - Another 30s video showing the earth"
echo " >> - Another 30s video showing the earth"
echo ""
echo " >> BLOCKABLE MIXED CONTENT"
echo " >> - A paragraph saying 'Script loaded over HTTP'"
echo " >> - A red text paragraph"
echo " >> - An iframe saying 'HTTP'"
echo " >> - A paragraph saying 'Fetch succeeded over: HTTP"
echo " >> - A paragraph saying 'XHR succeeded over: HTTP"
echo " >> - A background image saying 'HTTP'"
echo " >> - An object tag showing 'served over HTTP'"
echo " >> - A paragraph saying 'Beacon send attempted over HTTP"
echo " >> - A red image"
echo " >> - A text in the Comic Sans font"
echo "-------"
echo "Press enter to continue"
read -r

adb shell am force-stop com.test.httpcontenttester
sleep 1


echo "---------"
echo "EXPERIMENT 5/5"
echo ""
echo "=> Opening data with setMixedContentMode to MIXED_CONTENT_NEVER_ALLOW"
adb shell am start -n com.test.httpcontenttester/.MainActivity --es data "1" --es mc "1" --es nav "1"
echo " >> The website should display the following:"
echo ""
echo " >> UPGRADABLE MIXED CONTENT"
echo " >> - An image showing 'HTTP'"
echo " >> - A 30s video showing the earth"
echo " >> - 2 one second audios of a cat miaowing"
echo " >> - Another 30s video showing the earth"
echo " >> - Another 30s video showing the earth"
echo ""
echo " >> BLOCKABLE MIXED CONTENT"
echo " >> - A paragraph saying 'Script loaded over HTTP'"
echo " >> - A red text paragraph"
echo " >> - An iframe saying 'HTTP'"
echo " >> - A paragraph saying 'Fetch succeeded over: HTTP"
echo " >> - A paragraph saying 'XHR succeeded over: HTTP"
echo " >> - A background image saying 'HTTP'"
echo " >> - An object tag showing 'served over HTTP'"
echo " >> - A paragraph saying 'Beacon send attempted over HTTP"
echo " >> - A red image"
echo " >> - A text in the sans-serif font"
echo "-------"
echo "Press enter to continue"
read -r 

echo "FINISHED"
