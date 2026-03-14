from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_sv_edi_communication_mode = fields.Selection(
        string="Modo de Comunicación",
        related="company_id.l10n_sv_edi_communication_mode",
        readonly=False,
        groups="base.group_system",
        help="Seleccione el modo de comunicación para la transmisión de documentos electrónicos. "
        "Puede ser directa con el Ministerio de Hacienda o a través de un proxy configurado.",
    )

    l10n_sv_edi_proxy_url = fields.Char(
        string="URL del Proxy",
        related="company_id.l10n_sv_edi_proxy_url",
        # default="http://proxydte.tagre.pe/",
        readonly=False,
        groups="base.group_system",
        help="Ingrese la URL del proxy que se utilizará para la comunicación con el Ministerio de Hacienda. "
        "Este campo solo es relevante si selecciona 'A través de Proxy' como modo de comunicación.",
    )
    l10n_sv_edi_signer_url = fields.Char(
        string="URL del Firmador",
        related="company_id.l10n_sv_edi_signer_url",
        # default="http://firmaelectronicadte.tagre.pe:8222",
        readonly=False,
        groups="base.group_system",
        help="Ingrese la URL del servicio de firmador que se utilizará para firmar los documentos electrónicos. "
        "Si utilizará el firmador de tagre.pe: Para dar de alta el usuario, contacte a: +51993433774 ó soporte@tagre.pe"
        "Debe proveer el certificado .crt correspondiente para la configuración.",
    )
    l10n_sv_edi_environment = fields.Selection(
        string="Entorno",
        readonly=False,
        related="company_id.l10n_sv_edi_environment",
    )
    l10n_sv_edi_prior_validation = fields.Boolean(
        string="Validacion Previa del DTE",
        related="company_id.l10n_sv_edi_prior_validation",
        readonly=False,
        help="Validación previa del dte antes de transmitirlo al Ministerio de Hacienda",
    )
    l10n_sv_edi_token = fields.Char(string="Token", related="company_id.l10n_sv_edi_token")
    l10n_sv_edi_username = fields.Char(string="Usuario", related="company_id.l10n_sv_edi_username", readonly=False)
    l10n_sv_edi_password = fields.Char(string="Client Secret (API)", related="company_id.l10n_sv_edi_password", readonly=False)
    l10n_sv_edi_cert_private_key = fields.Char(
        related="company_id.l10n_sv_edi_cert_private_key",
        string="Clave privada del certificado",
        readonly=False,
    )
    l10n_sv_edi_cert_public_key = fields.Char(
        related="company_id.l10n_sv_edi_cert_public_key",
        string="Clave publica del certificado",
        readonly=False,
    )

    l10n_sv_edi_certificate_id = fields.Many2one(
        related="company_id.l10n_sv_edi_certificate_id", readonly=False, domain="[('company_id','=',company_id),('is_valid','=',True)]"
    )
