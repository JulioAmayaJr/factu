from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_sv_edi_economic_activity_id = fields.Many2one(
        comodel_name="l10n_sv.cat.019",
        string="Código de Actividad Económica",
        # compute="_compute_l10n_sv_edi_economic_activity_id",
    )

    def _aoeu(self):
        self.name = "uaoeu"

    # @api.depends("is_company")
    # def _compute_l10n_sv_edi_economic_activity_id(self):
    #     for rec in self:
    #         if not rec.is_company:
    #             rec.l10n_sv_edi_economic_activity_id = False
