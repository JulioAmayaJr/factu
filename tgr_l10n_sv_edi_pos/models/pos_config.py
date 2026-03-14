from odoo import models, fields


class PosConfig(models.Model):
    _inherit = "pos.config"

    l10n_sv_edi_cod_pos_mh = fields.Char("Código de Punto de Venta M.H.", help="Código Proporcionado por el Ministerio de Hacionda del SV.")
    l10n_sv_edi_cod_pos = fields.Char("Código de Punto de Venta")
    l10n_sv_edi_receipt_header = fields.Text("Encabezado ticket SV")

    def get_limited_partners_loading(self):
        partner_ids = super().get_limited_partners_loading()
        if (self.env.ref("tgr_l10n_sv_edi_pos.partner_sv_cf").id,) not in partner_ids:
            partner_ids.append((self.env.ref("tgr_l10n_sv_edi_pos.partner_sv_cf").id,))
        return partner_ids
