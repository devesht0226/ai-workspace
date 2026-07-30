#!/usr/bin/env bash
# Generate self-signed TLS certs for local HTTPS demos.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/deploy/nginx/certs"
mkdir -p "$OUT"
openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout "$OUT/privkey.pem" \
  -out "$OUT/fullchain.pem" \
  -subj "/CN=localhost/O=AI Workspace/C=US"
echo "Wrote $OUT/fullchain.pem and $OUT/privkey.pem"
