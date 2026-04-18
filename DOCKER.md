# Odoo 18 en Docker (proyecto factu)

## Estructura

- `docker-compose.yml` — PostgreSQL 16 + Odoo 18 (imagen extendida con dependencias Python del EDI).
- `docker/Dockerfile` — basado en `odoo:18.0`, instala `pyjwt`, `xmltodict` (y reintenta con `pip` si hace falta).
- `docker/odoo.conf` — `addons_path`, credenciales DB, logs a consola (`logfile=-` en comando), `admin_passwd` de desarrollo.
- `scripts/start.sh` — orquesta build, DB `factu_db`, instalación de módulos, arranque de Odoo.
- `scripts/validate_cde.sh` — comprobaciones SQL + `odoo shell` + búsqueda en código.
- `addons/` — opcional (ver `addons/README.md`).

Los módulos `tgr_l10n_sv`, `tgr_l10n_sv_edi` y `tgr_l10n_sv_edi_pos` permanecen en la raíz del repo; el volumen `.:/mnt/extra-addons` los expone a Odoo.

## Requisitos

Docker Engine + Docker Compose v2.

## Comandos exactos

### Arranque completo (primera vez o actualización)

```bash
chmod +x scripts/start.sh scripts/validate_cde.sh
./scripts/start.sh
./scripts/validate_cde.sh
```

### Levantar sin reinstalar (solo contenedores)

```bash
docker compose up -d
```

### Ver logs

```bash
docker compose logs -f odoo
docker compose logs -f db
```

### Entrar al contenedor Odoo

```bash
docker compose exec odoo bash
```

### Entrar a PostgreSQL

```bash
docker compose exec db psql -U odoo -d factu_db
```

### Reinicio limpio (borra volúmenes: BD y filestore)

```bash
docker compose down -v
```

### Actualizar solo módulos tgr (con Odoo parado o en run one-off)

```bash
docker compose run --rm --no-deps odoo odoo \
  -c /etc/odoo/odoo.conf \
  -d factu_db \
  --stop-after-init \
  -u tgr_l10n_sv,tgr_l10n_sv_edi,tgr_l10n_sv_edi_pos \
  --without-demo=all \
  --logfile=-
```

### Búsquedas en código (host)

```bash
rg "tipoDte" tgr_l10n_sv_edi
rg "\"15\"" tgr_l10n_sv tgr_l10n_sv_edi
rg "CDE|donación|donation|l10n_sv\.dte\.cd" tgr_l10n_sv_edi
```

## URLs y credenciales

- Odoo: `http://localhost:8069`
- PostgreSQL: `localhost:5432`, usuario `odoo`, contraseña `odoo`, base `factu_db`
- Master password (crear/gestionar BDs desde UI): `docker/odoo.conf` → `admin_passwd` (cambiar en producción).

## Notas

- La prueba de `generate_json` en `validate_cde.sh` solo corre en profundidad si ya existe una factura con tipo de documento **15**; si no, indica `SKIP_JSON` (las demás comprobaciones siguen siendo obligatorias).

## Errores reales encontrados al montar (y corrección)

1. **Odoo 18 / vista `account_move_views.xml`:** `column_invisible="parent.l10n_latam_document_type_id.code != '15'"` provoca `ParseError: Invalid composed field ... in modifier 'column_invisible'`. Se corrigió con el campo relacionado `tgr_l10n_sv_latam_doc_type_code` en `account.move` y el uso de `parent.tgr_l10n_sv_latam_doc_type_code` en la lista de líneas (y el grupo CDE usa el mismo campo en `invisible`).

2. **Imagen base `odoo:18.0`:** `pip` emitió avisos sobre metadata de `charset_normalizer` en site-packages; no impidió la instalación de `pyjwt` / `xmltodict`.

3. **`odoo shell`:** avisos de fuentes PDF (`Can't find .pfb for face 'Courier'`); no afectan la validación CDE.
