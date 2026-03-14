from odoo import fields, models


class ResCity(models.Model):
    _inherit = "res.city"

    l10n_sv_code = fields.Char(
        string="Codigo", help="Codigo de Municipio en el estandar CAT-013 v1.1 MH"
    )
