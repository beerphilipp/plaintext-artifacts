#!/usr/bin/env bash
#
# Selects N random APKs available on the remote download host and rsyncs them
# into <DIR>.
#
# Usage:
#   download_apks.sh <DIR> [COUNT]
#
# Expects an SSH private key mounted at /root/.ssh/webview_key.

set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "Usage: $0 <DIR> [COUNT]" >&2
    exit 1
fi

DEST_DIR=$1
COUNT=${2:-500}
MOUNTED_KEY=/root/.ssh/webview_key
KEY=/tmp/webview_key
REMOTE="dl@download.st1.secpriv.wien:"
APP_LIST=/tmp/apps.txt

if [[ ! -f "$MOUNTED_KEY" ]]; then
    echo "ERROR: SSH key not found at $MOUNTED_KEY. Mount it with -v /path/to/webview_key:$MOUNTED_KEY:ro" >&2
    exit 1
fi

cp "$MOUNTED_KEY" "$KEY"
chmod 600 "$KEY"
mkdir -p "$DEST_DIR"

echo "Selecting $COUNT random APKs from $REMOTE ..."
FULL_LIST=/tmp/all_apps.txt
rsync -e "ssh -p 22111 -i $KEY -o StrictHostKeyChecking=accept-new" -dn \
    --out-format="%n" "$REMOTE" . > "$FULL_LIST"

echo "Remote listing: $(wc -l < "$FULL_LIST") entries"

SHUFFLED=/tmp/shuffled.txt
sort -R "$FULL_LIST" > "$SHUFFLED"
head -n "$COUNT" "$SHUFFLED" > "$APP_LIST"

echo "Selected $(wc -l < "$APP_LIST") APKs"

echo "Downloading $(wc -l < "$APP_LIST") APKs into $DEST_DIR ..."
rsync -e "ssh -p 22111 -i $KEY -o StrictHostKeyChecking=accept-new" -avvxz \
    --progress \
    --files-from "$APP_LIST" \
    "$REMOTE" "$DEST_DIR"

echo "Done. App list saved to $APP_LIST."
