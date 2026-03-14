from odoo import models, fields
from odoo.addons.tgr_l10n_sv_edi.models.account_move import CAT_007_TIPO_GENERACION


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    tgr_l10n_sv_edi_tipo_generacion = fields.Selection(
        selection=CAT_007_TIPO_GENERACION,
        string="Tipo de Generacion del documento relacionado",
        default="2",
        required=True,
        help="Tipo de generación del documento tributario relacionado",
    )

    def _prepare_default_reversal(self, move):
        # OVERRIDE
        values = super()._prepare_default_reversal(move)
        if (
            move.company_id.country_id.code == "SV"
            and move.journal_id.l10n_latam_use_documents
        ):
            values.update(
                {
                    "tgr_l10n_sv_edi_tipo_generacion": self.tgr_l10n_sv_edi_tipo_generacion
                    or "2",
                    # "l10n_latam_document_type_id": self.l10n_latam_document_type_id.id
                    # or self.env.ref("l10n_pe.document_type07").id,
                }
            )
        return values
