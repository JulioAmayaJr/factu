from odoo import fields, models

# CAT_009_ESTABLISHMENT = [
#     ("01", "[01] Sucursal"),
#     ("02", "[02] Casa Matriz"),
#     ("04", "[04] Bodega"),
#     ("07", "[07] Patio"),
# ]


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_sv_edi_establishment_type = fields.Selection(
        related="partner_id.l10n_sv_edi_establishment_type",
        string="Tipo de Establecimiento",
        store=True,
        readonly=False,
        help="Codigo de tipo de establecimiento CAT-009 V1.1 MH",
    )

    def _localization_use_documents(self):
        # OVERRIDE
        self.ensure_one()
        return (
            self.account_fiscal_country_id.code == "SV"
            or super()._localization_use_documents()
        )
