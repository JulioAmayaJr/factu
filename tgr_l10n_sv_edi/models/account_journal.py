from odoo import api, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.depends("l10n_latam_use_documents")
    def _compute_edi_format_ids(self):
        return super()._compute_edi_format_ids()
