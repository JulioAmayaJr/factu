from odoo import fields, models
from odoo.api import readonly


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_sv_edi_communication_mode = fields.Selection(
        selection=[("direct", "Directo con MH"), ("proxy", "Servidor proxy")],
        string="Modo de Comunicación",
        groups="base.group_system",
    )

    l10n_sv_edi_proxy_url = fields.Char(
        string="URL del Proxy",
        groups="base.group_system",
    )
    l10n_sv_edi_signer_url = fields.Char(
        string="URL del Firmador",
        groups="base.group_system",
    )
    l10n_sv_edi_environment = fields.Selection(
        selection=[("test", "Pruebas"), ("prod", "Producción")],
        default="test",
        string="Entorno",
        groups="base.group_system",
    )
    l10n_sv_edi_prior_validation = fields.Boolean(
        string="Validacion Previa del DTE",
        help="Validación previa del dte antes de transmitirlo al Ministerio de Hacienda",
    )
    l10n_sv_edi_token = fields.Char(string="Token", groups="base.group_system")
    l10n_sv_edi_username = fields.Char(string="Client ID", groups="base.group_system")
    l10n_sv_edi_password = fields.Char(string="Client Secret (API)", groups="base.group_system")

    l10n_sv_edi_certificate_id = fields.Many2one(string="Certififado (SV)", store=True, readonly=False, comodel_name="l10n_sv.certificate")

    l10n_sv_edi_economic_activity_id = fields.Many2one(
        related="partner_id.l10n_sv_edi_economic_activity_id",
        string="Código de Actividad Económica",
        store=True,
        readonly=False,
        help="Código de Actividad Económica CAT-019 V1.1 MH",
    )
    l10n_sv_edi_cod_estable = fields.Char("Código de Establecimiento", size=4)
    l10n_sv_edi_cod_estable_mh = fields.Char("Código de Establecimiento MH", size=4)
    l10n_sv_edi_cert_private_key = fields.Char(
        "Clave privada del certificado",
        groups="base.group_system",
        store=True,
        readonly=False,
    )
    l10n_sv_edi_cert_public_key = fields.Char(
        "Clave publica del certificado",
        groups="base.group_system",
        store=True,
        readonly=False,
    )

    def l10n_sv_edi_get_root_company(self):
        self.ensure_one()
        if self.parent_id:
            root_id = int(self.parent_path.split("/")[0])
            root_company = self.env["res.company"].browse(root_id)
            return root_company
        return self


#    l10n_sv_edi_establishment_type = fields.Selection(
#        related="partner_id.l10n_sv_edi_establishment_type", string="Tipo de Establecimiento"
#    )
