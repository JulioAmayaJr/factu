#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-factu}"
echo "[factu] docker compose down -v (borra volúmenes de PostgreSQL y filestore)"
docker compose down -v
