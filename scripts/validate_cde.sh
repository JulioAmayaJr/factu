#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-factu}"

log() { echo "[validate_cde] $*"; }
err() { echo "[validate_cde][ERROR] $*" >&2; }

if ! docker compose ps --status running --services 2>/dev/null | grep -q '^odoo$'; then
  err "El contenedor odoo no está en ejecución. Ejecute: ./scripts/start.sh"
  exit 1
fi

if ! docker compose exec -T db psql -U odoo -d factu_db -tAc "SELECT 1" >/dev/null 2>&1; then
  err "No se puede conectar a la base factu_db."
  exit 1
fi

log "Comprobando módulos instalados (SQL)..."
docker compose exec -T db psql -U odoo -d factu_db -c \
  "SELECT name, state FROM ir_module_module WHERE name IN ('tgr_l10n_sv','tgr_l10n_sv_edi','tgr_l10n_sv_edi_pos') ORDER BY name;"

BAD="$(docker compose exec -T db psql -U odoo -d factu_db -tAc \
  "SELECT COUNT(*) FROM ir_module_module WHERE name IN ('tgr_l10n_sv','tgr_l10n_sv_edi','tgr_l10n_sv_edi_pos') AND state='installed'" | tr -d '[:space:]')"
if [[ "${BAD:-0}" != "3" ]]; then
  err "Los tres módulos tgr_* deben estar en state=installed (encontrados: ${BAD:-0})."
  exit 1
fi

log "Comprobando tipo de documento 15 (SQL)..."
docker compose exec -T db psql -U odoo -d factu_db -c \
  "SELECT id, code, name FROM l10n_latam_document_type WHERE code = '15';"

CNT="$(docker compose exec -T db psql -U odoo -d factu_db -tAc \
  "SELECT COUNT(*) FROM l10n_latam_document_type WHERE code = '15'" | tr -d '[:space:]')"
if [[ "${CNT:-0}" -lt 1 ]]; then
  err "No existe l10n_latam.document.type con code=15."
  exit 1
fi

log "Búsqueda en código (host): tipoDte / 15 / CDE..."
if command -v rg >/dev/null 2>&1; then
  rg -n "tipoDte|\"15\"|l10n_sv\.dte\.cd|Comprobante de donación|fe-cd-v1" tgr_l10n_sv tgr_l10n_sv_edi tgr_l10n_sv_edi_pos --glob "*.py" --glob "*.xml" --glob "*.json" || true
else
  grep -RIn "tipoDte\|\"15\"\|l10n_sv.dte.cd\|fe-cd-v1" tgr_l10n_sv tgr_l10n_sv_edi tgr_l10n_sv_edi_pos --include="*.py" --include="*.xml" --include="*.json" 2>/dev/null || true
fi

log "Ejecutando comprobaciones en odoo shell..."
if ! docker compose exec -T odoo odoo shell -c /etc/odoo/odoo.conf -d factu_db <"$ROOT/scripts/shell_validate_cde.py"; then
  err "Falló odoo shell (validación Python)."
  exit 1
fi

log "Prueba opcional de generate_json (si ya existe factura con tipo 15)..."
docker compose exec -T odoo odoo shell -c /etc/odoo/odoo.conf -d factu_db <<'EOS'
import json

move = env["account.move"].search([("l10n_latam_document_type_id.code", "=", "15")], limit=1)
if not move:
    print("SKIP_JSON: no hay facturas con tipo 15; cree una en UI para probar generate_json con datos reales.")
else:
    payload = env["l10n_sv.dte.cd"].generate_json(move, {"environment": "test"})
    assert payload.get("identificacion", {}).get("tipoDte") == "15"
    assert "donatario" in payload and "donante" in payload
    assert payload.get("cuerpoDocumento")
    print("JSON_CDE_OK:", json.dumps(payload["identificacion"], indent=2, ensure_ascii=False))
EOS

log "Validación completada."
