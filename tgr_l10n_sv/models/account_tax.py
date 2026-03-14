from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"
    l10n_sv_edi_tax_code = fields.Selection(
        [
            ("20", "[20] - Impuesto al Valor Agregado 13%"),
            ("C3", "[C3] - Impuesto al Valor Agregado (exportaciones) 0%"),
            ("59", "[59] - Turismo: por alojamiento (5%)"),
            ("71", "[71] - Turismo: salida del país por vía aérea $7.00"),
            ("D1", "[D1] - FOVIAL ($0.20 Ctvs. por galón)"),
            ("C8", "[C8] - COTRANS ($0.10 Ctvs. por galón)"),
            ("D5", "[D5] - Otras tasas casos especiales"),
            ("D4", "[D4] - Otros impuestos casos especiales"),
        ],
        string="CAT- 15: Código de tributos",
    )
