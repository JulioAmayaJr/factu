from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tgr_l10n_sv_edi_tipo_donacion = fields.Selection(
        [("1", "Tipo 1"), ("2", "Tipo 2"), ("3", "Tipo 3")],
        string="Tipo donación (CDE)",
        default="1",
    )
