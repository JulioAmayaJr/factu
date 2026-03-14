from odoo import api, fields, models


class L10n_latamIdentificationType(models.Model):
    _inherit = "l10n_latam.identification.type"

    l10n_sv_vat_code = fields.Char()

    @api.depends("country_id")
    def _compute_display_name(self):
        multi_localization = len(self.search([]).mapped("country_id")) > 1
        for rec in self:
            vat_code_display = (
                f"[{rec.l10n_sv_vat_code}] " if rec.l10n_sv_vat_code else ""
            )
            rec.display_name = "{}{}{}".format(
                vat_code_display,
                rec.name,
                multi_localization
                and rec.country_id
                # and " (%s)" % rec.country_id.code
                and f"({rec.country_id.code})"
                or "",
            )
