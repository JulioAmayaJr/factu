from odoo import api, models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_sv_edi_cod_pos_mh = fields.Char(related="pos_config_id.l10n_sv_edi_cod_pos_mh", readonly=False, size=4)
    l10n_sv_edi_cod_pos = fields.Char(related="pos_config_id.l10n_sv_edi_cod_pos", readonly=False, size=15)

    l10n_sv_edi_receipt_header = fields.Text(related="pos_config_id.l10n_sv_edi_receipt_header", readonly=False)
