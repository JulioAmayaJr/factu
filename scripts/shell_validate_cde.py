# Ejecutar con: odoo shell -c /etc/odoo/odoo.conf -d factu_db < este_archivo
import sys

checks = []

dt = env["l10n_latam.document.type"].search([("code", "=", "15")], limit=1)
checks.append(("l10n_latam.document.type código 15", bool(dt)))

try:
    env["l10n_sv.dte.cd"]
    checks.append(("Modelo abstracto l10n_sv.dte.cd en env", True))
except KeyError:
    checks.append(("Modelo abstracto l10n_sv.dte.cd en env", False))

im = env["ir.model"].search([("model", "=", "l10n_sv.dte.cd")], limit=1)
checks.append(("ir.model registro l10n_sv.dte.cd", bool(im)))

fmt = env["account.edi.format"].search([("code", "=", "sv_dte_1_0")], limit=1)
checks.append(("account.edi.format sv_dte_1_0", bool(fmt)))

import os

schema = "/mnt/extra-addons/tgr_l10n_sv_edi/static/svfe-json-schemas/fe-cd-v1.json"
checks.append(("Archivo schema fe-cd-v1.json", os.path.isfile(schema)))

for label, ok in checks:
    print(f"{'OK' if ok else 'FAIL'}: {label}")

if not all(c[1] for c in checks):
    sys.exit(1)

src = "/mnt/extra-addons/tgr_l10n_sv_edi/models/account_edi_format.py"
routing_ok = False
if os.path.isfile(src):
    with open(src, encoding="utf-8") as f:
        body = f.read()
    routing_ok = 'elif tipo_dte == "15"' in body and "l10n_sv.dte.cd" in body
checks.append(("Enrutamiento Python tipo 15 -> l10n_sv.dte.cd", routing_ok))
print(f"{'OK' if routing_ok else 'FAIL'}: Enrutamiento Python tipo 15 -> l10n_sv.dte.cd")

if not routing_ok:
    sys.exit(1)

print("VALIDACION_CDE: todas las comprobaciones obligatorias pasaron.")
