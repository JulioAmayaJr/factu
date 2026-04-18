#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-factu}"

log() { echo "[factu] $*"; }
err() { echo "[factu][ERROR] $*" >&2; }

log "Construyendo imagen Odoo (deps Python EDI)..."
docker compose build odoo

log "Levantando PostgreSQL..."
docker compose up -d db

log "Esperando healthcheck de PostgreSQL..."
for i in $(seq 1 90); do
  if docker compose exec -T db pg_isready -U odoo -d postgres >/dev/null 2>&1; then
    log "PostgreSQL listo."
    break
  fi
  if [[ "$i" -eq 90 ]]; then
    err "PostgreSQL no respondió a tiempo."
    docker compose logs db | tail -n 80
    exit 1
  fi
  sleep 1
done

DBEXISTS="$(docker compose exec -T db psql -U odoo -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='factu_db'" 2>/dev/null | tr -d '[:space:]' || true)"
if [[ "${DBEXISTS:-}" != "1" ]]; then
  log "Creando base de datos factu_db..."
  docker compose exec -T db createdb -U odoo factu_db
else
  log "La base factu_db ya existe."
fi

TABLE_EXISTS=""
if docker compose exec -T db psql -U odoo -d factu_db -tAc "SELECT 1" >/dev/null 2>&1; then
  TABLE_EXISTS="$(docker compose exec -T db psql -U odoo -d factu_db -tAc "SELECT to_regclass('public.ir_module_module')" 2>/dev/null | tr -d '[:space:]' || true)"
fi

log "Instalando / actualizando módulos (puede tardar varios minutos)..."
if [[ "${TABLE_EXISTS:-}" == "ir_module_module" ]]; then
  if ! docker compose run --rm --no-deps odoo odoo \
    -c /etc/odoo/odoo.conf \
    -d factu_db \
    --stop-after-init \
    -u tgr_l10n_sv,tgr_l10n_sv_edi,tgr_l10n_sv_edi_pos \
    --without-demo=all \
    --logfile=-; then
    err "Fallo la actualización de módulos. Últimas líneas de log arriba."
    exit 1
  fi
else
  if ! docker compose run --rm --no-deps odoo odoo \
    -c /etc/odoo/odoo.conf \
    -d factu_db \
    --stop-after-init \
    -i base,account,point_of_sale,tgr_l10n_sv,tgr_l10n_sv_edi,tgr_l10n_sv_edi_pos \
    --without-demo=all \
    --logfile=-; then
    err "Fallo la instalación inicial. Revise dependencias y logs."
    exit 1
  fi
fi

log "Iniciando servicio Odoo (HTTP 8069)..."
docker compose up -d odoo

log "Esperando respuesta HTTP en 8069..."
for i in $(seq 1 120); do
  if curl -sf "http://127.0.0.1:8069/web/database/manager" >/dev/null 2>&1 \
    || curl -sf "http://127.0.0.1:8069/web/login" >/dev/null 2>&1 \
    || curl -sf "http://127.0.0.1:8069/web" >/dev/null 2>&1; then
    log "Odoo responde."
    break
  fi
  if [[ "$i" -eq 120 ]]; then
    err "Odoo no respondió en 8069."
    docker compose logs odoo | tail -n 120
    exit 1
  fi
  sleep 1
done

log "Listo."
log "  URL:     http://localhost:8069"
log "  Base:    factu_db"
log "  Master:  ver admin_passwd en docker/odoo.conf (cambiar en producción)"
log "  Validar: ./scripts/validate_cde.sh"
