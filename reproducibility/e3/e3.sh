#!/usr/bin/env bash
#
# Script: e3.sh
#
# Description:
#   Executes experiment 3.
#
# Usage:
#   ./e3.sh DB_SNAPSHOT_DIR GPLAY_SQLITE
#
# Arguments:
#   DB_SNAPSHOT_DIR  Path to the MongoDB snapshot directory (required).
#   GPLAY_SQLITE     Path to the gplay.sqlite database file (required).
#                    Mounted into the jupyter container at /data/gplay.sqlite.

abort() {
    echo "ERROR: $1" >&2
    exit 1
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../../" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yaml"
EVALUATION_SCRIPTS_DIR="${ROOT_DIR}/evaluation_scripts"

[[ -n "${1:-}" ]] || abort "DB_SNAPSHOT_DIR argument is required. Usage: ./e3.sh DB_SNAPSHOT_DIR GPLAY_SQLITE"
DB_SNAPSHOT_DIR="$1"
[[ -d "$DB_SNAPSHOT_DIR" ]] || abort "Database snapshot directory not found: $DB_SNAPSHOT_DIR"
MONGO_FILE_DIR="$DB_SNAPSHOT_DIR"
DATABASE_RESULT_DIR="$DB_SNAPSHOT_DIR"

[[ -n "${2:-}" ]] || abort "GPLAY_SQLITE argument is required. Usage: ./e3.sh DB_SNAPSHOT_DIR GPLAY_SQLITE"
GPLAY_SQLITE="$2"
[[ -f "$GPLAY_SQLITE" ]] || abort "GPlay SQLite database not found: $GPLAY_SQLITE"
GPLAY_SQLITE="$(cd "$(dirname "$GPLAY_SQLITE")" && pwd)/$(basename "$GPLAY_SQLITE")"
export GPLAY_SQLITE

echo "--------------------------------"
echo "Experiment 3"
echo "--------------------------------"

command -v docker >/dev/null || abort "Docker is not installed. Please install it to run this script."

[[ -f "$COMPOSE_FILE" ]] || abort "docker-compose.yaml not found at $COMPOSE_FILE"

echo "Starting docker-compose ..."
docker compose -f "$COMPOSE_FILE" up -d || abort "Failed to start docker compose stack"

create_index() {
    local collection="$1"
    local field="$2"
    docker exec webview_mongo mongosh --quiet "mongodb://localhost:27017/webview" \
        --eval "db.${collection}.createIndex({ ${field}: 1 })" >/dev/null \
        || abort "Failed to create index ${field} on ${collection}"
}

echo "- mongo-express is accessible at  http://localhost:8081"
echo "- MongoDB is running on mongodb://localhost:27019"



echo "Restoring webview database ..."
mongorestore --port 27019 --db webview --gzip "${DATABASE_RESULT_DIR}/webview-backup/webview"

echo "Restoring dynamic API calls ..."
mongorestore --port 27019 --db webview --gzip "${DATABASE_RESULT_DIR}/webview-dynamic-backup/webview"

echo "Restoring network logs ..."
mongorestore --port 27019 --db webview --gzip "${DATABASE_RESULT_DIR}/webview-network-backup/webview"


echo ""
echo "=> Open **http://localhost:8888**"
echo ""