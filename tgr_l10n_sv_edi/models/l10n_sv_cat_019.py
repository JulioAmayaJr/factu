from odoo import api, fields, models


class L10nSvCat019(models.Model):
    _name = "l10n_sv.cat.019"
    _description = "Código de Actividad Económica"
    _rec_names_search = ["code", "name"]

    code = fields.Char(string="Código", required=True)
    name = fields.Char(string="Nombre", required=True)
    active = fields.Boolean(string="Activo", default=True)
    _sql_constraints = [
        ("code_uniq", "unique (code)", "El código debe ser único"),
    ]

    @api.depends("code", "name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"[{rec.code}] {rec.name}"

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, f"[{rec.code}] {rec.name}"))
        return result
