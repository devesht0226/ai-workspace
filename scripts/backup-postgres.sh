#!/usr/bin/env bash
# Backup Postgres volume data via pg_dump.
set -euo pipefail
STAMP=$(date +%Y%m%d_%H%M%S)
OUT_DIR="${1:-./backups}"
mkdir -p "$OUT_DIR"
FILE="$OUT_DIR/aiworkspace_$STAMP.sql"
docker compose exec -T postgres pg_dump -U aiworkspace aiworkspace > "$FILE"
echo "Backup written to $FILE"
