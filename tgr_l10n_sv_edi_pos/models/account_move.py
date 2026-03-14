from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "pos.load.mixin"]

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        self.filtered(lambda am: am.sudo().pos_order_ids).edi_document_ids.filtered(
            lambda d: d.state == "to_send"
        )._process_documents_web_services(job_count=1)
        return posted

    def l10n_sv_edi_numero_control_values(self):
        res = super().l10n_sv_edi_numero_control_values()
        pos_config = self.env["pos.order"].search([("name", "=", self.ref)], limit=1)
        pos_config = pos_config.config_id if pos_config else None
        if pos_config:
            res["cod_pos_mh"] = pos_config.l10n_sv_edi_cod_pos_mh or "0000"
        return res

    @api.model
    def _load_pos_data_domain(self, data):
        result = super()._load_pos_data_domain(data)
        if self.env.company.country_id.code == "SV":
            return False
        return result

    @api.model
    def _load_pos_data_fields(self, config_id):
        result = super()._load_pos_data_fields(config_id)
        if self.env.company.country_id.code == "SV":
            return [
                "tgr_l10n_sv_edi_codigo_generacion",
                "tgr_l10n_sv_edi_numero_control",
                "tgr_l10n_sv_edi_sello_recibido",
                "tgr_l10n_sv_edi_barcode_image",
            ]
        return result
