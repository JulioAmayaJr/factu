from odoo import fields, models
from odoo.addons.tgr_l10n_sv_edi.models.account_move import CAT_024_TIPO_INVAlIDACION


class TgrL10nSvCancelWizard(models.TransientModel):
    _name = "tgr_l10n_sv_edi.cancel"
    _description = "Wizard to allow the cancelation of El Salvador"

    tgr_l10n_sv_edi_tipo_invalidacion = fields.Selection(
        selection=CAT_024_TIPO_INVAlIDACION, string="Tipo de Invalidación", default="2", copy=False
    )
    tgr_l10n_sv_edi_motivo_invalidacion = fields.Char(string="Motivo de Invalidación", copy=False)

    def button_cancel(self):
        self.ensure_one()
        moves = self.env["account.move"].browse(self._context.get("active_ids"))
        print(moves.name)
        moves.tgr_l10n_sv_edi_tipo_invalidacion = self.tgr_l10n_sv_edi_tipo_invalidacion
        moves.tgr_l10n_sv_edi_motivo_invalidacion = (
            self.tgr_l10n_sv_edi_motivo_invalidacion.strip() if self.tgr_l10n_sv_edi_motivo_invalidacion else False
        )
        moves.button_cancel_posted_moves()
        return True
