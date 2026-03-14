import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

CAT_009_ESTABLISHMENT = [
    ("01", "[01] Sucursal"),
    ("02", "[02] Casa Matriz"),
    ("04", "[04] Bodega"),
    ("07", "[07] Patio"),
]


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_sv_nrc = fields.Char(string="Número de Registro de Contribuyente")
    l10n_sv_district = fields.Many2one("l10n_sv.res.city.district", string="Distrito")
    l10n_sv_district_name = fields.Char(
        "Nombre de Distrito", related="l10n_sv_district.name"
    )

    l10n_sv_edi_establishment_type = fields.Selection(
        selection=CAT_009_ESTABLISHMENT, string="Tipo de Establecimiento"
    )

    @api.onchange("l10n_sv_district")
    def _onchange_l10n_sv_district(self):
        if self.l10n_sv_district:
            self.city_id = self.l10n_sv_district.city_id.id
            self.zip = self.l10n_sv_district.code

    @api.onchange("city_id")
    def _onchange_l10n_sv_district(self):
        if (
            self.city_id
            and self.l10n_sv_district.city_id
            and self.l10n_sv_district.city_id != self.city_id
        ):
            self.l10n_sv_district = False

    @api.model
    def _formatting_address_fields(self):
        # Retorno una lista de los campos de la direccion para usar es las direcciones
        return super()._formatting_address_fields() + ["l10n_sv_district_name"]

    @api.onchange("company_type")
    def _onchange_company_type(self):
        for rec in self:
            if rec.company_type == "person":
                rec.l10n_latam_identification_type_id = self.env[
                    "l10n_latam.identification.type"
                ].search([("l10n_sv_vat_code", "=", "13")], limit=1)
            else:
                self.l10n_latam_identification_type_id = self.env[
                    "l10n_latam.identification.type"
                ].search([("l10n_sv_vat_code", "=", "36")], limit=1)
