# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, api


class PosSession(models.Model):
    _inherit = "pos.session"

    @api.model
    def _load_pos_data_models(self, config_id):
        data = super()._load_pos_data_models(config_id)
        if self.env.company.country_id.code == "SV":
            data += ["l10n_sv.res.city.district", "l10n_latam.identification.type", "res.city", "account.move"]
        return data

    def _load_pos_data(self, data):
        data = super()._load_pos_data(data)
        if self.env.company.country_id.code == "SV":
            document_types = self.env["l10n_latam.document.type"].search_read(
                [("active", "=", True), ("country_id.code", "=", "SV"), ("code", "in", ["01", "03"])],
                ["id", "code", "internal_type", "display_name"],
            )
            data["data"][0]["_l10n_latam_document_type"] = [{"value": doc["code"], "name": doc["display_name"]} for doc in document_types]
            data["data"][0]["_default_l10n_latam_identification_type_id"] = self.env.ref("tgr_l10n_sv.it_dui").id
            data["data"][0]["_consumidor_final_anonimo_id"] = self.env.ref("tgr_l10n_sv_edi_pos.partner_sv_cf").id
        return data
