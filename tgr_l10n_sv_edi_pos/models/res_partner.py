# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import _, api, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.ondelete(at_uninstall=False)
    def _pe_unlink_except_master_data(self):
        consumidor_final_anonimo = self.env.ref("tgr_l10n_sv_edi_pos.partner_sv_cf")
        if consumidor_final_anonimo & self:
            raise UserError(
                _(
                    "No se puede eliminar el partner %s por que se requiere para el Punto de Venta de El Salvador.",
                    consumidor_final_anonimo.display_name,
                )
            )

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields = super()._load_pos_data_fields(config_id)
        if self.env.company.country_id.code == "SV":
            fields += ["city_id", "l10n_latam_identification_type_id", "l10n_sv_district"]
        return fields
