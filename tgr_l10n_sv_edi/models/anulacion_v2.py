import uuid
from datetime import datetime

from odoo import api, models
from pytz import timezone


class DteAnulacion(models.AbstractModel):
    _name = "l10n_sv.dte.anulacion"
    _inherit = "l10n_sv.dte.mixin"
    _description = "Documento de Anulación"

    name = "anulacion_v2"
    _version = 2

    @api.model
    def generate_json(self, invoice, credentials):
        return {
            "identificacion": self._get_identificacion(credentials),
            "emisor": self._get_emisor(invoice),
            "documento": self._get_documento(invoice),
            "motivo": self._get_motivo(invoice),
        }

    def _get_identificacion(self, credentials):
        return {
            "version": self._version,
            "ambiente": "01" if credentials["environment"] == "prod" else "00",
            "codigoGeneracion": str(uuid.uuid4()).upper(),
            "fecAnula": datetime.now(tz=timezone("America/El_Salvador")).strftime("%Y-%m-%d"),
            "horAnula": datetime.now(tz=timezone("America/El_Salvador")).strftime("%H:%M:%S"),
        }

    def _get_emisor(self, invoice):
        root_partner = invoice.company_id.sudo().l10n_sv_edi_get_root_company().partner_id
        partner = invoice.company_id.partner_id
        cod_estable = self._get_cod_estable(invoice)
        return {
            **cod_estable,
            "nit": root_partner.vat,
            "nombre": root_partner.name,
            "tipoEstablecimiento": partner.l10n_sv_edi_establishment_type if partner.l10n_sv_edi_establishment_type else "02",
            "nomEstablecimiento": partner.name,
            "codPuntoVentaMH": None,
            "codPuntoVenta": "0001",
            "telefono": partner.phone or None,
            "correo": partner.email or None,
        }

    def _get_documento(self, invoice):
        return {
            "tipoDte": invoice.l10n_latam_document_type_id.code or "",
            "codigoGeneracion": invoice.tgr_l10n_sv_edi_codigo_generacion or None,
            "selloRecibido": invoice.tgr_l10n_sv_edi_sello_recibido or None,
            "numeroControl": invoice.tgr_l10n_sv_edi_numero_control,
            "fecEmi": invoice.invoice_date.strftime("%Y-%m-%d"),
            "montoIva": invoice.amount_total,
            "codigoGeneracionR": None,
            "tipoDocumento": invoice.commercial_partner_id.l10n_latam_identification_type_id.l10n_sv_vat_code,
            "numDocumento": invoice.commercial_partner_id.vat or None,
            "nombre": invoice.commercial_partner_id.name,
            "telefono": invoice.commercial_partner_id.phone or None,
            "correo": invoice.commercial_partner_id.email or None,
        }

    def _get_motivo(self, invoice):
        curren_user = self.env.user
        user = curren_user.partner_id if curren_user else invoice.user_id.partner_id
        return {
            "tipoAnulacion": int(invoice.tgr_l10n_sv_edi_tipo_invalidacion) or None,
            "motivoAnulacion": invoice.tgr_l10n_sv_edi_motivo_invalidacion or None,
            "nombreResponsable": user.name or None,
            "tipDocResponsable": user.l10n_latam_identification_type_id.l10n_sv_vat_code or None,
            "numDocResponsable": user.vat or None,
            "nombreSolicita": user.name or None,
            "tipDocSolicita": user.l10n_latam_identification_type_id.l10n_sv_vat_code or None,
            "numDocSolicita": user.vat or None,
        }
