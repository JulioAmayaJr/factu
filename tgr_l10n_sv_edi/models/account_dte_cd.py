import re
from datetime import datetime
from zoneinfo import ZoneInfo

from odoo import api, models
from odoo.tools.float_utils import float_round


class CdDteDocument(models.AbstractModel):
    _name = "l10n_sv.dte.cd"
    _inherit = "l10n_sv.dte.mixin"
    _description = "Comprobante de donación electrónico"

    name = "fe-cd"
    _version = 1
    _tipoDte = "15"

    def _l10n_sv_edi_cd_clean_vat(self, vat):
        if not vat:
            return None
        return re.sub(r"[\s-]", "", str(vat))

    def _l10n_sv_edi_cd_clean_nit(self, vat):
        s = self._l10n_sv_edi_cd_clean_vat(vat)
        return s.upper() if s else None

    def _get_identificacion(self, invoice, credentials):
        return {
            "version": 1,
            "ambiente": "01" if credentials["environment"] == "prod" else "00",
            "tipoDte": self._tipoDte,
            "numeroControl": invoice.tgr_l10n_sv_edi_numero_control or "",
            "codigoGeneracion": invoice.tgr_l10n_sv_edi_codigo_generacion or "",
            "tipoModelo": 1,
            "tipoOperacion": 1,
            "fecEmi": invoice.invoice_date.strftime("%Y-%m-%d"),
            "horEmi": datetime.now(ZoneInfo("America/El_Salvador")).strftime("%H:%M:%S"),
            "tipoMoneda": "USD",
        }

    def _get_donatario(self, invoice):
        company = invoice.company_id
        partner = company.partner_id
        root_company = company.l10n_sv_edi_get_root_company()
        root_partner = root_company.partner_id
        cod_estable = self._get_cod_estable(invoice)
        return {
            "tipoDocumento": "36",
            "numDocumento": self._l10n_sv_edi_cd_clean_nit(root_partner.vat),
            "nrc": root_partner.l10n_sv_nrc or None,
            "nombre": root_partner.name,
            "codActividad": root_partner.l10n_sv_edi_economic_activity_id.code or None,
            "descActividad": root_partner.l10n_sv_edi_economic_activity_id.name or None,
            "nombreComercial": company.name or root_partner.name,
            "tipoEstablecimiento": (
                company.partner_id.l10n_sv_edi_establishment_type
                if company.partner_id.l10n_sv_edi_establishment_type
                else "02"
            ),
            "direccion": self._get_common_direccion(partner),
            "telefono": partner.phone,
            "correo": partner.email,
            **cod_estable,
            "codPuntoVentaMH": "P001",
            "codPuntoVenta": "0001",
        }

    def _get_donante(self, invoice):
        partner = invoice.commercial_partner_id
        tipo_doc = (
            partner.l10n_latam_identification_type_id.l10n_sv_vat_code
            if partner.l10n_latam_identification_type_id and partner.vat
            else None
        )
        cod_dom = int(invoice.tgr_l10n_sv_edi_cd_cod_domiciliado or "1")
        direccion = self._get_common_direccion(partner) if cod_dom == 1 else None
        act_code = partner.l10n_sv_edi_economic_activity_id.code if cod_dom == 1 else None
        act_name = partner.l10n_sv_edi_economic_activity_id.name if cod_dom == 1 else None
        tel = partner.phone or partner.mobile
        if tel and len(tel.strip()) < 8:
            tel = None
        mail = partner.email if partner.email and "@" in partner.email else None
        return {
            "tipoDocumento": tipo_doc,
            "numDocumento": self._l10n_sv_edi_cd_clean_vat(partner.vat) if partner.vat else None,
            "nrc": partner.l10n_sv_nrc or None,
            "nombre": partner.name,
            "codActividad": act_code,
            "descActividad": act_name,
            "direccion": direccion,
            "telefono": tel,
            "correo": mail,
            "codDomiciliado": cod_dom,
            "codPais": invoice.tgr_l10n_sv_edi_cd_cod_pais or "9300",
        }

    def _get_otros_documentos(self, invoice):
        return [
            {
                "codDocAsociado": int(invoice.tgr_l10n_sv_edi_cd_otros_cod or 1),
                "descDocumento": (invoice.tgr_l10n_sv_edi_cd_otros_desc or "").strip(),
                "detalleDocumento": (invoice.tgr_l10n_sv_edi_cd_otros_detalle or "").strip(),
            }
        ]

    def _get_cuerpo_documento(self, values):
        lines = []
        for item in values["invoice_line_vals_list"]:
            line = item["line"]
            tipo_don = int(line.tgr_l10n_sv_edi_tipo_donacion or "1")
            qty = line.quantity or 0.0
            subtotal = line.price_subtotal or 0.0
            valor_uni = float_round(subtotal / qty, 6) if qty else float_round(subtotal, 6)
            valor = float_round(subtotal, 6)
            depreciacion = 0.0 if tipo_don in (1, 3) else 0.0
            uni_medida = 99 if tipo_don in (1, 3) else (
                line.product_id.product_tmpl_id.uom_id.l10n_sv_edi_measure_unit_code or 99
                if line.product_id
                else 99
            )
            codigo = line.product_id.default_code if line.product_id and line.product_id.default_code else None
            lines.append(
                {
                    "numItem": item["index"],
                    "tipoDonacion": tipo_don,
                    "cantidad": qty,
                    "codigo": codigo,
                    "uniMedida": uni_medida,
                    "descripcion": (line.name or line.product_id.display_name or "Donación")[:1000],
                    "depreciacion": depreciacion,
                    "valorUni": valor_uni,
                    "valor": valor,
                }
            )
        return lines

    def _get_resumen(self, values):
        invoice = values["record"]
        pagos_src = values["invoice_date_due_vals_list"]
        if not pagos_src:
            pagos_src = [{"code": "01", "amount": invoice.amount_total}]
        total = invoice.amount_total or 0.0
        return {
            "valorTotal": float_round(total, 2),
            "totalLetras": str(invoice._l10n_sv_edi_amount_to_text()).replace("DOLLARS", "DÓLARES").replace("CENTS", "CENTAVOS")[
                :200
            ],
            "pagos": [
                {
                    "codigo": x["code"],
                    "montoPago": float_round(x["amount"], 2),
                    "referencia": None,
                }
                for x in pagos_src
            ],
        }

    @api.model
    def generate_json(self, invoice, credentials):
        values = self._l10n_sv_edi_get_dte_values(invoice)
        return {
            "identificacion": self._get_identificacion(invoice, credentials),
            "donatario": self._get_donatario(invoice),
            "donante": self._get_donante(invoice),
            "cuerpoDocumento": self._get_cuerpo_documento(values),
            "resumen": self._get_resumen(values),
            "otrosDocumentos": self._get_otros_documentos(invoice),
            "apendice": None,
        }
