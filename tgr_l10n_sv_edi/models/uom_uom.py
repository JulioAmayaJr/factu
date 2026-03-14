from odoo import fields, models


class UomUom(models.Model):
    _inherit = "uom.uom"

    l10n_sv_edi_measure_unit_code = fields.Integer(
        "Cod. Unidad de Medida", help="CAT - 014"
    )
