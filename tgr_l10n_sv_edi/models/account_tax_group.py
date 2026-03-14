from odoo import fields, models


class AccountTaxGroup(models.Model):
    _inherit = "account.tax.group"

    l10n_sv_edi_code = fields.Char("DTE Codigo")
