from odoo import fields, models


class ResCityDistrict(models.Model):
    _name = "l10n_sv.res.city.district"
    _description = "Distritos"
    _order = "name"

    name = fields.Char(string="Nombre", required=True)
    city_id = fields.Many2one("res.city", string="Municipio", required=True)
    code = fields.Char(string="Codigo")
